import time
import threading
import itertools
from google import genai
import logging
from cau_hinh import CauHinh

logger = logging.getLogger(__name__)

class _TokenBucket:
    """
    Token Bucket Rate Limiter cấp độ key.
    Mỗi key có 1 bucket riêng, giới hạn số request/phút.
    Cơ chế: Mỗi giây "nạp" thêm token, mỗi request "tiêu" 1 token.
    """
    def __init__(self, capacity: float, refill_rate: float):
        """
        capacity: Số request tối đa trong 1 burst (= RPM limit).
        refill_rate: Số token được nạp mỗi giây (= capacity / 60).
        """
        self.capacity = capacity
        self.tokens = capacity  # Bắt đầu đầy
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, timeout: float = 120.0) -> bool:
        """
        Chờ cho đến khi có token. Trả về True nếu lấy được, False nếu timeout.
        """
        deadline = time.monotonic() + timeout
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.last_refill = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

                # Tính thời gian chờ cho token tiếp theo
                wait_time = (1.0 - self.tokens) / self.refill_rate

            if time.monotonic() + wait_time > deadline:
                return False  # Timeout

            time.sleep(min(wait_time, 1.0))  # Sleep tối đa 1s rồi thử lại


class EmbeddingPool:
    """
    Global Rate Limiter & Key Rotator cho Embedding.
    V41.1: OpenAI (text-embedding-3-large) làm PRIMARY.
    Gemini (Token Bucket per-key) làm FALLBACK dự phòng.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EmbeddingPool, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.keys = CauHinh.GEMINI_API_KEYS
        if not self.keys:
            raise ValueError("No Gemini API keys found.")

        # --- Token Bucket per key ---
        # V41: Gemini Embedding 2: 100 RPM, 1K RPD, 30K TPM per project
        # Đặt 90 RPM (an toàn 90% của 100) để luôn có headroom
        self.rpm_per_key = 90
        self.buckets = {}
        for key in self.keys:
            self.buckets[key] = _TokenBucket(
                capacity=self.rpm_per_key,
                refill_rate=self.rpm_per_key / 60.0  # token/giây
            )

        # Key rotation
        self._key_index = 0
        self._rotation_lock = threading.Lock()

        # Dead key tracking (Gemini)
        self.dead_keys = set()
        self.gemini_dead = False
        self.dead_time = 0.0
        
        # Dead tracking (OpenAI)
        self.openai_dead = False
        
        logger.info(f"[EmbeddingPool] Initialized with OpenAI as Primary, Gemini as Fallback ({len(self.keys)} keys)")

    def _next_key(self) -> str:
        """Round-robin chọn key tiếp theo (bỏ qua dead keys)."""
        with self._rotation_lock:
            alive_keys = [k for k in self.keys if k not in self.dead_keys]
            if not alive_keys:
                return None
            self._key_index = (self._key_index + 1) % len(alive_keys)
            return alive_keys[self._key_index]

    def _find_available_key(self, timeout: float = 30.0) -> str:
        """
        Tìm key có token khả dụng. Thử tất cả key theo round-robin,
        nếu không key nào có token ngay, chờ key đầu tiên có token.
        """
        alive_keys = [k for k in self.keys if k not in self.dead_keys]
        if not alive_keys:
            return None

        # Pass 1: Thử nhanh tất cả key (timeout = 0, không chờ)
        start_idx = self._key_index % len(alive_keys)
        for i in range(len(alive_keys)):
            idx = (start_idx + i) % len(alive_keys)
            key = alive_keys[idx]
            bucket = self.buckets[key]
            if bucket.acquire(timeout=0.05):  # Thử ngay, gần như không chờ
                with self._rotation_lock:
                    self._key_index = (idx + 1) % len(alive_keys)
                return key

        # Pass 2: Tất cả key đều hết token → chờ key đầu tiên có token
        key = alive_keys[start_idx]
        bucket = self.buckets[key]
        logger.debug(f"[EmbeddingPool] All keys busy. Waiting for token on key ...{key[-4:]}")
        if bucket.acquire(timeout=timeout):
            return key

        return None  # Timeout hoàn toàn

    def embed_content(self, texts: list, model_name: str = "models/text-embedding-004", max_retries: int = None, primary_provider: str = "openai"):
        """
        V41.2: Hỗ trợ linh hoạt chuyển đổi PRIMARY provider (openai hoặc gemini).
        Trả về list các vector (list of floats). Nếu thất bại trả về None.
        """
        if not texts:
            return []

        def call_openai():
            if getattr(self, "openai_dead", False): 
                return None
            try:
                from openai import OpenAI
                o_client = OpenAI(api_key=CauHinh.OPENAI_API_KEY)
                res = o_client.embeddings.create(
                    input=texts,
                    model="text-embedding-3-large",
                    dimensions=768  # Ép về 768 chiều để đồng nhất định dạng
                )
                return [d.embedding for d in res.data]
            except Exception as oe:
                err_str = str(oe).lower()
                logger.error(f"[EmbeddingPool] OpenAI call failed: {oe}")
                if "quota" in err_str or "insufficient_quota" in err_str or "429" in err_str:
                    logger.error("[EmbeddingPool] OpenAI is out of quota/rate-limited. Marking as DEAD.")
                    self.openai_dead = True
                return None

        def call_gemini():
            nonlocal max_retries
            if max_retries is None: 
                max_retries = len(self.keys)

            if getattr(self, "gemini_dead", False):
                if time.time() - getattr(self, "dead_time", 0) > 12 * 3600:
                    logger.info("[EmbeddingPool] 12 hours passed. Reactivating Gemini keys.")
                    self.gemini_dead = False
                    self.dead_keys.clear()
                else:
                    return None

            retries = 0
            while retries < max_retries:
                current_key = self._find_available_key(timeout=65.0)
                if current_key is None:
                    logger.warning("[EmbeddingPool] No available Gemini key (all tokens exhausted). Retrying...")
                    retries += 1
                    continue

                try:
                    client = genai.Client(api_key=current_key)
                    res = client.models.embed_content(
                        model=model_name,
                        contents=texts,
                        config={'output_dimensionality': 768}
                    )

                    vectors = []
                    if isinstance(res, list):
                        for r in res:
                            vectors.append(r.values)
                    else:
                        for e in res.embeddings:
                            vectors.append(e.values)
                    return vectors

                except Exception as e:
                    err_msg = str(e).lower()
                    if "403" in err_msg or "permission_denied" in err_msg:
                        logger.error(f"[EmbeddingPool] Key ...{current_key[-4:]} is DEAD (403 PERMISSION_DENIED). Adding to dead_keys.")
                        self.dead_keys.add(current_key)
                        if len(self.dead_keys) >= len(self.keys):
                            logger.error("[EmbeddingPool] ALL Gemini keys are DEAD (403).")
                            self.gemini_dead = True
                            self.dead_time = time.time()
                            break
                        continue
                    elif "429" in err_msg or "quota" in err_msg or "exhausted" in err_msg:
                        if "perday" in err_msg or "limit: 1000" in err_msg:
                            self.dead_keys.add(current_key)
                            if len(self.dead_keys) >= len(self.keys):
                                logger.error("[EmbeddingPool] ALL Gemini keys are DEAD (Daily Limit).")
                                self.gemini_dead = True
                                self.dead_time = time.time()
                                break

                        import re
                        match = re.search(r"retrydelay': '(\d+)s'", err_msg) or re.search(r"retry in (\d+\.?\d*)s", err_msg)
                        logger.warning(f"[EmbeddingPool] Key ...{current_key[-4:]} rate limited (429). (Attempt {retries+1}/{max_retries}). Skipping...")
                        
                        bucket = self.buckets[current_key]
                        with bucket.lock:
                            bucket.tokens = 0.0
                            bucket.last_refill = time.monotonic()
                        
                        time.sleep(1.0)
                    else:
                        logger.error(f"[EmbeddingPool] Error: {e}")
                        time.sleep(2)

                    retries += 1
            return None

        # Routing logic
        if primary_provider == "openai":
            res = call_openai()
            if res is not None: return res
            logger.warning("[EmbeddingPool] OpenAI failed. Switching to Gemini Fallback.")
            res = call_gemini()
            if res is not None: return res
        else:
            res = call_gemini()
            if res is not None: return res
            logger.warning("[EmbeddingPool] Gemini failed. Switching to OpenAI Fallback.")
            res = call_openai()
            if res is not None: return res

        logger.error("[EmbeddingPool] BOTH primary and fallback providers failed.")
        return None

# Khởi tạo singleton
embedding_pool = EmbeddingPool()
