# -*- coding: utf-8 -*-
import os
import base64
import hashlib
from cryptography.fernet import Fernet

def get_fernet_key():
    secret = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    key_32 = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_32)

def ma_hoa_key(raw_text: str) -> str:
    if not raw_text:
        return ""
    try:
        f = Fernet(get_fernet_key())
        return f.encrypt(raw_text.strip().encode("utf-8")).decode("utf-8")
    except Exception:
        return ""

def giai_ma_key(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    
    current_val = cipher_text
    # Hỗ trợ giải mã đệ quy để tự động khôi phục nếu khóa bị mã hóa nhiều lần
    for _ in range(5):
        if not current_val.startswith("gAAAAA"):
            return current_val
            
        decrypted = ""
        # 1. Thử bằng FLASK_SECRET_KEY hiện tại
        try:
            f = Fernet(get_fernet_key())
            decrypted = f.decrypt(current_val.encode("utf-8")).decode("utf-8")
        except Exception:
            pass
            
        if not decrypted:
            # 2. Thử bằng dev-secret-key-123
            try:
                key_32 = hashlib.sha256(b"dev-secret-key-123").digest()
                f = Fernet(base64.urlsafe_b64encode(key_32))
                decrypted = f.decrypt(current_val.encode("utf-8")).decode("utf-8")
            except Exception:
                pass
                
        if not decrypted:
            # 3. Thử bằng dev-secret-key mặc định
            try:
                key_32 = hashlib.sha256(b"dev-secret-key").digest()
                f = Fernet(base64.urlsafe_b64encode(key_32))
                decrypted = f.decrypt(current_val.encode("utf-8")).decode("utf-8")
            except Exception:
                pass
                
        if decrypted:
            current_val = decrypted
        else:
            break
            
    return current_val if not current_val.startswith("gAAAAA") else ""

class CauHinhMeta(type):
    def lay_tu_csdl(cls, khoa):
        try:
            from mo_hinh import CauHinhHeThong
            item = CauHinhHeThong.query.filter_by(khoa=khoa).first()
            if item and item.gia_tri:
                api_keys_to_encrypt = ["OPENAI_API_KEY", "GEMINI_API_KEYS", "SEPAY_API_KEY", "VNPAY_HASH_SECRET"]
                if khoa in api_keys_to_encrypt:
                    if not item.gia_tri.startswith("gAAAAA"):
                        return item.gia_tri
                    decrypted = giai_ma_key(item.gia_tri)
                    if decrypted:
                        return decrypted
                    # Nếu giải mã hoàn toàn thất bại, trả về None để dùng giá trị tĩnh fallback
                    return None
                return item.gia_tri
        except Exception:
            pass
        return None

    @property
    def OPENAI_API_KEY(cls):
        val = cls.lay_tu_csdl("OPENAI_API_KEY")
        return val if val is not None else cls._OPENAI_API_KEY

    @OPENAI_API_KEY.setter
    def OPENAI_API_KEY(cls, val):
        cls._OPENAI_API_KEY = val

    @property
    def GEMINI_API_KEYS(cls):
        val = cls.lay_tu_csdl("GEMINI_API_KEYS")
        if val is not None:
            return [k.strip() for k in val.split(",") if k.strip()]
        return cls._GEMINI_API_KEYS

    @GEMINI_API_KEYS.setter
    def GEMINI_API_KEYS(cls, val):
        cls._GEMINI_API_KEYS = val

    @property
    def SEPAY_API_KEY(cls):
        val = cls.lay_tu_csdl("SEPAY_API_KEY")
        return val if val is not None else cls._SEPAY_API_KEY

    @SEPAY_API_KEY.setter
    def SEPAY_API_KEY(cls, val):
        cls._SEPAY_API_KEY = val

    @property
    def VNPAY_HASH_SECRET(cls):
        val = cls.lay_tu_csdl("VNPAY_HASH_SECRET")
        return val if val is not None else cls._VNPAY_HASH_SECRET

    @VNPAY_HASH_SECRET.setter
    def VNPAY_HASH_SECRET(cls, val):
        cls._VNPAY_HASH_SECRET = val

    @property
    def VNPAY_TMN_CODE(cls):
        val = cls.lay_tu_csdl("VNPAY_TMN_CODE")
        return val if val is not None else cls._VNPAY_TMN_CODE

    @VNPAY_TMN_CODE.setter
    def VNPAY_TMN_CODE(cls, val):
        cls._VNPAY_TMN_CODE = val

    @property
    def VNPAY_PAYMENT_URL(cls):
        val = cls.lay_tu_csdl("VNPAY_PAYMENT_URL")
        return val if val is not None else cls._VNPAY_PAYMENT_URL

    @VNPAY_PAYMENT_URL.setter
    def VNPAY_PAYMENT_URL(cls, val):
        cls._VNPAY_PAYMENT_URL = val

    @property
    def VNPAY_RETURN_URL(cls):
        val = cls.lay_tu_csdl("VNPAY_RETURN_URL")
        return val if val is not None else cls._VNPAY_RETURN_URL

    @VNPAY_RETURN_URL.setter
    def VNPAY_RETURN_URL(cls, val):
        cls._VNPAY_RETURN_URL = val

    @property
    def PAYMENT_VNPAY_ACTIVE(cls):
        val = cls.lay_tu_csdl("PAYMENT_VNPAY_ACTIVE")
        if val is not None:
            return val == "True"
        return cls._PAYMENT_VNPAY_ACTIVE

    @PAYMENT_VNPAY_ACTIVE.setter
    def PAYMENT_VNPAY_ACTIVE(cls, val):
        cls._PAYMENT_VNPAY_ACTIVE = val

    @property
    def PAYMENT_SEPAY_ACTIVE(cls):
        val = cls.lay_tu_csdl("PAYMENT_SEPAY_ACTIVE")
        if val is not None:
            return val == "True"
        return cls._PAYMENT_SEPAY_ACTIVE

    @PAYMENT_SEPAY_ACTIVE.setter
    def PAYMENT_SEPAY_ACTIVE(cls, val):
        cls._PAYMENT_SEPAY_ACTIVE = val

    @property
    def SEPAY_ACCOUNT_NUMBER(cls):
        val = cls.lay_tu_csdl("SEPAY_ACCOUNT_NUMBER")
        return val if val is not None else cls._SEPAY_ACCOUNT_NUMBER

    @SEPAY_ACCOUNT_NUMBER.setter
    def SEPAY_ACCOUNT_NUMBER(cls, val):
        cls._SEPAY_ACCOUNT_NUMBER = val

    @property
    def SEPAY_BANK_BRAND(cls):
        val = cls.lay_tu_csdl("SEPAY_BANK_BRAND")
        return val if val is not None else cls._SEPAY_BANK_BRAND

    @SEPAY_BANK_BRAND.setter
    def SEPAY_BANK_BRAND(cls, val):
        cls._SEPAY_BANK_BRAND = val

    @property
    def SEPAY_WEB_NAME(cls):
        val = cls.lay_tu_csdl("SEPAY_WEB_NAME")
        return val if val is not None else cls._SEPAY_WEB_NAME

    @SEPAY_WEB_NAME.setter
    def SEPAY_WEB_NAME(cls, val):
        cls._SEPAY_WEB_NAME = val

    @property
    def SEPAY_XOR_KEY(cls):
        val = cls.lay_tu_csdl("SEPAY_XOR_KEY")
        if val is not None:
            try:
                return int(val, 16) if "0x" in str(val).lower() else int(val)
            except Exception:
                pass
        return cls._SEPAY_XOR_KEY

    @SEPAY_XOR_KEY.setter
    def SEPAY_XOR_KEY(cls, val):
        cls._SEPAY_XOR_KEY = val

class CauHinh(metaclass=CauHinhMeta):
    # Flask
    KHOA_BI_MAT = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

    # Mail Config (SMTP)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "phanvantho082019@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "ylifjkrtmpzpbomh")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "phanvantho082019@gmail.com")

    # OpenAI (Fallback keys)
    _OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Gemini (Fallback keys)
    _GEMINI_API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", "")).split(",") if k.strip()]

    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")           # Model mạnh — dùng cho việc cần độ chính xác cao
    GEMINI_MODEL_LITE = os.getenv("GEMINI_MODEL_LITE", "gemini-2.5-flash-lite")  # Model nhẹ — dùng cho hầu hết Supervisor tasks
    GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")

    # Local Generator Config
    LOCAL_API_BASE = os.getenv("LOCAL_API_BASE", "http://localhost:11434/v1")
    LOCAL_MODEL = os.getenv("LOCAL_MODEL", "gemma:2b")

    # Supervisor Architecture Config
    SEARCH_MODEL = os.getenv("SEARCH_MODEL", "gpt-4o")  # Model thông minh dùng cho Crawler/Spider
    WRITER_MODEL = os.getenv("WRITER_MODEL", "gpt-4o-mini")  # Model viết bài
    SUPERVISOR_MODEL_LITE = os.getenv("SUPERVISOR_MODEL_LITE", "gemini-2.5-flash-lite")
    SUPERVISOR_MODEL_PRO = os.getenv("SUPERVISOR_MODEL_PRO", "gemini-2.5-flash")

    GEMINI_AUDIT_RATE = float(os.getenv("GEMINI_AUDIT_RATE", "1.0"))       # 100% audit (vì dùng GPT-4o-mini làm writer)
    MAX_REWRITE_ATTEMPTS = int(os.getenv("MAX_REWRITE_ATTEMPTS", "2"))     # Số lần rewrite tối đa / chương
    SUPERVISOR_OUTLINE_CHECK = os.getenv("SUPERVISOR_OUTLINE_CHECK", "true").lower() == "true"  # Có kiểm tra outline không



    # Wikipedia crawling limits
    SO_TRANG_HAT_GIONG = int(os.getenv("SO_TRANG_HAT_GIONG", "10"))       # seed pages (tổng vi+en)
    SO_TRANG_LIEN_KET = int(os.getenv("SO_TRANG_LIEN_KET", "30"))        # linked pages (depth=1)
    SO_DOAN_THAM_KHAO = int(os.getenv("SO_DOAN_THAM_KHAO", "120"))      # top passages gửi cho AI (token-saving)

    # Passage chunking
    DO_DAI_DOAN_MIN = int(os.getenv("DO_DAI_DOAN_MIN", "800"))
    DO_DAI_DOAN_MAX = int(os.getenv("DO_DAI_DOAN_MAX", "1500"))
    CAT_TREN_MOI_TRANG = int(os.getenv("CAT_TREN_MOI_TRANG", "12000"))   # cắt tối đa ký tự mỗi trang

    # Output folders
    THU_MUC_DU_LIEU = os.getenv("THU_MUC_DU_LIEU", "du_lieu")
    THU_MUC_CACHE = os.path.join(THU_MUC_DU_LIEU, "bo_nho_dem")
    THU_MUC_DAU_RA = os.path.join(THU_MUC_DU_LIEU, "dau_ra")

    THU_MUC_JSON = os.path.join(THU_MUC_DAU_RA, "json")
    THU_MUC_PDF = os.path.join(THU_MUC_DAU_RA, "pdf")
    THU_MUC_DOCX = os.path.join(THU_MUC_DAU_RA, "docx")

    # UI defaults (Relaxed for dynamic generation)
    MAC_DINH_SO_CHUONG_MIN = int(os.getenv("MAC_DINH_SO_CHUONG_MIN", "3"))
    MAC_DINH_SO_CHUONG_MAX = int(os.getenv("MAC_DINH_SO_CHUONG_MAX", "25"))

    # Production timeouts (V23.1)
    API_TIMEOUT = 60.0
    CHAPTER_TIMEOUT = 300.0
    JOB_TIMEOUT = 1200.0  # 20 minutes hard watchdog

    # =========================================================================
    # EKRE V26.2 - ADAPTIVE THRESHOLD & SAFE DEGRADATION CONFIG
    # =========================================================================

    # --- Hard Floors (tuyệt đối không xuống thấp hơn) ---
    EKRE_MIN_SIM_FLOOR = 0.30       # Ngưỡng tương đồng tối thiểu tuyệt đối
    EKRE_MIN_QUALITY_FLOOR = 0.5     # V26.2.1: Recalibrated cho formula (sim^2)*log(len)

    # --- Adaptive Similarity Floors (theo Complexity) ---
    EKRE_SIM_FLOORS = {
        "high":   0.35,   # Chủ đề khó: Bắt đầu từ 0.35, có thể hạ xuống 0.30
        "medium": 0.40,   # Chủ đề trung bình: Bắt đầu từ 0.40
        "low":    0.45,   # Chủ đề phổ thông: Bắt đầu từ 0.45
    }

    # --- Adaptive Noise Brake (MIN_AVG_SIM theo Complexity) ---
    EKRE_MIN_AVG_SIM = {
        "high":   0.30,   # Topic khó → chấp nhận avg_sim thấp hơn
        "medium": 0.32,   # Topic bình thường
        "low":    0.34,   # Topic dễ → yêu cầu avg_sim cao hơn
    }

    # --- Adaptive Loop Config ---
    EKRE_MAX_RELAXATION_ATTEMPTS = 4   # Số lần thử giãn chuẩn tối đa
    EKRE_LOW_RATIO_BRAKE = 0.50        # Dừng nếu >50% docs là low_priority

    # --- Standard Quality Thresholds (Reweighted: sim^2 * log(len)) ---
    # Output range: ~0.5 (poor) → ~2.0 (ok) → ~5.0 (great) → ~10 (excellent)
    EKRE_QUALITY_STANDARD = 1.5        # Ngưỡng tiêu chuẩn (đã hiệu chỉnh V26.2.1)
    EKRE_QUALITY_RESCUE    = 0.8       # Ngưỡng cứu hộ (Rescue Mode)

    # --- Target Yield theo Quy mô ---
    EKRE_TARGET_YIELD = {
        "can_ban":   8,    # Cơ bản: 8 docs
        "tieu_chuan": 15,  # Tiêu chuẩn: 15 docs
        "chuyen_sau": 25,  # Chuyên sâu: 25 docs
    }

    # --- Diversity Control ---
    EKRE_MAX_CHUNKS_PER_SOURCE = 3  # Tối đa 3 chunks từ cùng 1 nguồn

    # VNPAY Config
    _VNPAY_TMN_CODE = os.getenv("VNPAY_TMN_CODE", "V2ZFH4ZT")
    _VNPAY_HASH_SECRET = os.getenv("VNPAY_HASH_SECRET", "V830F79D7834Q4M5F9VCZY5XFCWEWWUA")
    _VNPAY_PAYMENT_URL = os.getenv("VNPAY_PAYMENT_URL", "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html")
    _VNPAY_RETURN_URL = os.getenv("VNPAY_RETURN_URL", "http://localhost:5000/payment/callback")

    # SePay Config
    _SEPAY_API_KEY = os.getenv("SEPAY_API_KEY", "")
    _SEPAY_ACCOUNT_NUMBER = os.getenv("SEPAY_ACCOUNT_NUMBER", "0327152710")
    _SEPAY_BANK_BRAND = os.getenv("SEPAY_BANK_BRAND", "MBBank")
    _SEPAY_WEB_NAME = os.getenv("SEPAY_WEB_NAME", "GTAI")
    _SEPAY_XOR_KEY = int(os.getenv("SEPAY_XOR_KEY", "0x5EAFB"), 16) if os.getenv("SEPAY_XOR_KEY") else 0x5EAFB

    # Toggle payments active status
    _PAYMENT_VNPAY_ACTIVE = os.getenv("PAYMENT_VNPAY_ACTIVE", "True") == "True"
    _PAYMENT_SEPAY_ACTIVE = os.getenv("PAYMENT_SEPAY_ACTIVE", "True") == "True"

    # Phí token của các chế độ biên soạn
    PHI_TOKEN_AUTO = int(os.getenv("PHI_TOKEN_AUTO", "1"))
    PHI_TOKEN_EXPERT = int(os.getenv("PHI_TOKEN_EXPERT", "2"))
    PHI_TOKEN_CREATIVE = int(os.getenv("PHI_TOKEN_CREATIVE", "3"))
