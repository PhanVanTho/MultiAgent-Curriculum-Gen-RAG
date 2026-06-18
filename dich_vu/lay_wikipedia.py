# -*- coding: utf-8 -*-
# EKRE V26.2 - Adaptive Threshold & Safe Degradation
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib.parse import quote
import time
import math
import statistics
import random
import os
import json
import logging
import threading
import numpy as np
import re
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import uuid
import random
from openai import OpenAI
from cau_hinh import CauHinh
from .lam_sach_van_ban import remove_diacritics

logger = logging.getLogger(__name__)

# --- CACHE HỆ THỐNG (V23.1 Production-Ready) ---
WIKI_CACHE = {}
WIKI_LOCK = threading.Lock()
OUTLINE_CACHE = {} # Cache cho outline theo topic
OUTLINE_LOCK = threading.Lock()
SEED_CACHE = {} # Cache cho Truth Seed Extraction (V27)
SEED_LOCK = threading.Lock()

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# --- UTILS ---
def dich_tai_lieu_en_sang_vi(text: str, api_key_openai: str) -> str:
    if not text or not api_key_openai:
        return text
    try:
        from openai import OpenAI
        from concurrent.futures import ThreadPoolExecutor
        client = OpenAI(api_key=api_key_openai, max_retries=1)
        chunks = []
        chunk_size = 3500
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i+chunk_size])
            
        def translate_chunk(index, chunk):
            if len(chunk.strip()) < 10:
                return index, ""
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional academic translator. Translate the following English Wikipedia content into natural, accurate, and formal academic Vietnamese. Preserve markdown format, numbers, proper names (e.g. Formula 1, Michael Schumacher, BRM), and formulas. Do not explain or add notes."},
                        {"role": "user", "content": chunk}
                    ],
                    temperature=0.2,
                    max_tokens=1500,
                    timeout=25.0
                )
                return index, resp.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"[CROSS-TRANSLATE] Error translating chunk {index}: {e}")
                return index, chunk

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(translate_chunk, idx, chunk) for idx, chunk in enumerate(chunks)]
            for future in futures:
                results.append(future.result())
        
        results.sort(key=lambda x: x[0])
        translated_chunks = [r[1] for r in results if r[1]]
        return "\n\n".join(translated_chunks)
    except Exception as e:
        logger.warning(f"[CROSS-TRANSLATE] Error translating EN doc chunk: {e}")
        return text


def _cat_text(text: str, max_chars: int):
    text = "\n".join([ln.strip() for ln in (text or "").splitlines() if ln.strip()])
    return text[:max_chars]

def safe_parse_json(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        return None

def score_knowledge_base(docs):
    """V35.1: Coverage score ưu tiên đa dạng nguồn hơn độ dài.
    Công thức: (unique_sources * 15) + (total_chars / 5000)
    - Trước: 5 bài × 35K = 224 điểm (quá cao, Spider không kích hoạt)
    - Sau: 5 bài × 35K = 75 + 35 = 110 điểm (hợp lý hơn)
    """
    if not docs: return 0
    total_chars = sum(len(d.get("text", "")) for d in docs)
    unique_titles = len(set(d.get("title", "Unknown") for d in docs))
    return (unique_titles * 15) + (total_chars / 5000)

def hard_rule_filter(title: str, content: str):
    if not title or not content: return True
    low_t = title.lower()
    low_c = content.lower()
    if title.replace(".","").replace(" ","").isdigit(): return True
    # Đã nâng cấp Disambiguation Filter đa ngôn ngữ
    forbidden_types = ["disambiguation", "danh sách", "list of", "phim", "movie", "định hướng", "may refer to", "có các nghĩa sau"]
    if any(x in low_t for x in forbidden_types): return True
    if any(x in low_c for x in ["may refer to:", "có thể là:", "định hướng"]) and len(low_c) < 1000: return True
    # V26.2: Nới lỏng ngưỡng độ dài xuống 400 (từ 500)
    if len(content) < 400: return True
    return False


# =============================================================================
# EKRE V26.2 - ADAPTIVE HELPERS
# =============================================================================

def detect_topic_complexity(topic: str, api_key: str, search_model: str = None) -> str:
    """
    Dùng OpenAI để phân loại độ phức tạp của chủ đề:
      - 'high'   : Chuyên sâu, kỹ thuật cao, ít nguồn (VD: Topological Quantum Computing)
      - 'medium' : Phổ biến trong học thuật, nguồn trung bình (VD: Machine Learning)
      - 'low'    : Phổ thông, dễ tìm nguồn (VD: World War II)
    Fallback: 'medium' nếu gọi API lỗi.
    """
    if not api_key:
        return "medium"
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=search_model or CauHinh.SEARCH_MODEL,
            messages=[
                {"role": "system", "content": "You are a knowledge classifier. Return ONLY one word: 'high', 'medium', or 'low'."},
                {"role": "user", "content": f"Classify the academic topic complexity for Wikipedia retrieval: '{topic}'.\n- 'high': niche, technical, sparse Wikipedia coverage\n- 'medium': standard academic topic\n- 'low': broad, popular, rich Wikipedia coverage\nReply with only one word."}
            ],
            max_tokens=5,
            temperature=0
        )
        result = resp.choices[0].message.content.strip().lower()
        if result in ("high", "medium", "low"):
            return result
    except Exception as e:
        logger.warning(f"[EKRE] Complexity detection failed: {e}. Defaulting to 'medium'.")
    return "medium"


def get_similarity_floor(complexity: str) -> float:
    """Lấy ngưỡng tương đồng ban đầu dựa trên độ phức tạp chủ đề."""
    return CauHinh.EKRE_SIM_FLOORS.get(complexity, 0.40)


def get_relaxation_step(yield_count: int, target_min: int) -> float:
    """
    Tính bước giãn chuẩn thông minh dựa trên mức độ thiếu hụt dữ liệu.
    - Thiếu nhiều (>70%) → giãn mạnh (0.03)
    - Thiếu vừa (>40%)  → giãn trung bình (0.02)
    - Gần đủ (<40%)     → giãn nhẹ (0.01)
    """
    if target_min <= 0:
        return 0.02
    deficit_ratio = max(0, (target_min - yield_count) / target_min)
    if deficit_ratio > 0.70:
        return 0.03
    elif deficit_ratio > 0.40:
        return 0.02
    else:
        return 0.01


def compute_quality_score(doc: dict) -> float:
    """
    V26.2: Công thức Reweighted Quality Score.
    score = (relevance_score^2) * log(text_length)
    Ưu tiên tính liên quan hơn độ dài, phù hợp với RAG production.
    """
    sim = doc.get("relevance_score", 0)
    text_len = max(1, len(doc.get("text", "")))
    return (sim ** 2) * math.log(text_len)


def _apply_adaptive_yield_gate(
    raw_docs: list,
    topic: str,
    api_key_openai: str,
    quy_mo: str,
    complexity: str,
    fetch_title_func,
    ai_titles: list,
    truth_seed: dict = None
) -> tuple:
    """
    EKRE V26.2.1 - Adaptive Yield Gate với Safe Degradation.

    QUAN TRỌNG: Nhận full raw_docs (chưa lọc) để mỗi iteration có thể 
    chạy hybrid_semantic_filter với ngưỡng thấp hơn trên toàn bộ tập dữ liệu.

    Quy trình:
    1. Chạy hybrid_semantic_filter trên raw_docs với ngưỡng hiện tại.
    2. Nếu thiếu dữ liệu → giảm ngưỡng từng bước nhỏ.
    3. Kiểm tra 3 phanh an toàn sau mỗi vòng.
    4. Trả về (filtered_docs, analytics_dict)
    """
    from dich_vu.vector_search import precompute_embeddings, hybrid_semantic_filter_cached

    target_min    = CauHinh.EKRE_TARGET_YIELD.get(quy_mo, 15)
    min_sim_floor = CauHinh.EKRE_MIN_SIM_FLOOR
    min_quality   = CauHinh.EKRE_MIN_QUALITY_FLOOR
    min_avg_sim   = CauHinh.EKRE_MIN_AVG_SIM.get(complexity, 0.32)
    max_attempts  = CauHinh.EKRE_MAX_RELAXATION_ATTEMPTS
    low_ratio_limit = CauHinh.EKRE_LOW_RATIO_BRAKE
    quality_std   = CauHinh.EKRE_QUALITY_STANDARD

    current_sim_threshold = get_similarity_floor(complexity)
    current_quality       = float(quality_std)
    quality_floor         = float(CauHinh.EKRE_QUALITY_RESCUE)

    analytics = {
        "relaxation_attempts": 0,
        "stop_reason": "INITIAL",
        "avg_sim": 0.0,
        "median_sim": 0.0,
        "std_sim": 0.0,
        "low_priority_count": 0,
        "confidence_score": 0.0,
    }

    allow_last_attempt = False
    filtered = []
    re_scored = []

    # --- EKRE V27: Cache Embeddings (Save ~80% API cost) ---
    logger.info(f"[ADAPTIVE] Precomputing embeddings for {len(raw_docs)} docs...")
    main_v, sub_v, doc_vectors = precompute_embeddings(raw_docs, topic, topic, api_key_openai)
    
    if main_v is None:
        logger.error("[ADAPTIVE] Embedding API completely failed.")
        analytics["stop_reason"] = "EMBEDDING_API_FAILED"
        return [], analytics

    for attempt in range(max_attempts + 1):  # +1 cho Soft Landing
        analytics["relaxation_attempts"] = attempt

        # --- 1. Chạy hybrid_semantic_filter_cached trên TOÀN BỘ raw_docs với ngưỡng mới ---
        re_scored = hybrid_semantic_filter_cached(
            raw_docs, main_v, sub_v, doc_vectors, topic, 
            threshold=current_sim_threshold, truth_seed=truth_seed
        )

        # --- 2. Apply Quality Score (Reweighted formula) ---
        priority_filtered = []
        low_priority_docs = []
        for doc in re_scored:
            q_score = compute_quality_score(doc)
            doc["quality_score"] = q_score
            if q_score >= current_quality:
                doc["is_low_priority"] = False
                priority_filtered.append(doc)
            elif q_score >= min_quality:
                # Soft Filter: không xóa, đánh dấu low_priority
                doc["is_low_priority"] = True
                low_priority_docs.append(doc)

        # Gộp: normal trước, low_priority sau
        current_batch = priority_filtered + low_priority_docs
        yield_count   = len(current_batch)
        low_count     = len(low_priority_docs)
        low_ratio     = low_count / max(1, yield_count)

        # --- 3. Tính các Metrics ---
        sims = [d.get("relevance_score", 0) for d in current_batch]
        avg_sim    = statistics.mean(sims) if sims else 0.0
        median_sim = statistics.median(sims) if sims else 0.0
        std_sim    = statistics.stdev(sims) if len(sims) > 1 else 0.0
        
        # V27: Top-K Coverage Score for Confidence
        good_sims = sorted([d.get("relevance_score", 0) for d in priority_filtered], reverse=True)
        best_doc_sim = good_sims[0] if good_sims else (max(sims) if sims else 0.0)
        
        # Lấy điểm trung bình của Top K (K=3)
        top_k = 3
        if good_sims:
            top_k_sims = good_sims[:top_k]
            avg_top_k = sum(top_k_sims) / top_k
        else:
            avg_top_k = 0.0
            
        coverage_score = avg_top_k # Coverage lúc này dựa vào chất lượng Top K
        
        # Công thức mới: Kết hợp sức mạnh của doc tốt nhất và mức độ phủ của Top K
        confidence = best_doc_sim * min(1.0, coverage_score)

        analytics.update({
            "avg_sim": round(avg_sim, 4),
            "median_sim": round(median_sim, 4),
            "std_sim": round(std_sim, 4),
            "low_priority_count": low_count,
            "confidence_score": round(confidence, 4),
        })

        logger.info(
            f"[ADAPTIVE] Attempt={attempt} | Sim≥{current_sim_threshold:.3f} | "
            f"Yield={yield_count}/{target_min} | AvgSim={avg_sim:.3f} | "
            f"LowRatio={low_ratio:.2f} | Confidence={confidence:.3f}"
        )

        # --- 4. Kiểm tra điều kiện PASS ---
        is_quality_ok = avg_sim >= min_avg_sim and yield_count >= target_min
        if is_quality_ok:
            filtered = current_batch
            analytics["stop_reason"] = "TARGET_MET"
            logger.info(f"[ADAPTIVE] ✅ TARGET_MET. Confidence={confidence:.3f}")
            break

        # Giữ lại batch tốt nhất nếu đây là lần cuối (Soft Landing)
        if allow_last_attempt:
            filtered = current_batch
            analytics["stop_reason"] = "HARD_FLOOR_REACHED"
            logger.warning(f"[ADAPTIVE] 🛑 HARD_FLOOR_REACHED after Soft Landing. Confidence={confidence:.3f}")
            break

        # --- 5. Phanh an toàn (Noise Brakes) ---
        if avg_sim < min_avg_sim and yield_count > 0:
            filtered = current_batch
            analytics["stop_reason"] = "NOISE_BRAKE_AVG_SIM"
            logger.warning(
                f"[ADAPTIVE] 🔴 NOISE_BRAKE_AVG_SIM: avg_sim={avg_sim:.3f} < {min_avg_sim}. Halting."
            )
            break

        if low_ratio > low_ratio_limit and yield_count > 0:
            filtered = current_batch
            analytics["stop_reason"] = "NOISE_BRAKE_LOW_RATIO"
            logger.warning(
                f"[ADAPTIVE] 🔴 NOISE_BRAKE_LOW_RATIO: {low_ratio:.2f} > {low_ratio_limit}. Halting."
            )
            break

        if attempt >= max_attempts:
            filtered = current_batch
            analytics["stop_reason"] = "MAX_ATTEMPTS_REACHED"
            logger.warning(f"[ADAPTIVE] ⚠️ MAX_ATTEMPTS_REACHED. Confidence={confidence:.3f}")
            break

        # --- 6. Giãn ngưỡng (Step-down) ---
        step = get_relaxation_step(yield_count, target_min)
        new_sim = current_sim_threshold - step
        new_quality = max(min_quality, current_quality * 0.9)

        # Kiểm tra Soft Landing
        if new_sim <= min_sim_floor:
            new_sim = min_sim_floor
            allow_last_attempt = True  # Cho phép 1 lần thử cuối ở đáy
            logger.info(f"[ADAPTIVE] 🟡 Approaching Hard Floor. Enabling Soft Landing for last attempt.")

        current_sim_threshold = max(min_sim_floor, new_sim)
        current_quality       = new_quality
        logger.info(
            f"[ADAPTIVE] ↘ Relaxing thresholds → Sim={current_sim_threshold:.3f}, Quality={current_quality:.1f} (step={step})"
        )

    # Nếu vòng lặp kết thúc không có kết quả nào
    if not filtered and re_scored:
        filtered = re_scored
        analytics["stop_reason"] = "FALLBACK_ACCEPT_ALL"
        logger.warning("[ADAPTIVE] ⚠️ No docs passed gates. Accepting all scored docs as fallback.")

    logger.info(
        f"[ADAPTIVE] Final → StopReason={analytics['stop_reason']} | "
        f"Yield={len(filtered)} | Confidence={analytics['confidence_score']:.3f} | "
        f"LowPriority={analytics['low_priority_count']}"
    )
    return filtered, analytics

def keyword_overlap(q: str, doc_title: str) -> bool:
    """Kiểm tra giao thoa từ khóa (normalized) giữa query và title."""
    q_norm = remove_diacritics(q).lower()
    t_norm = remove_diacritics(doc_title).lower()
    q_words = set(re.findall(r'\w+', q_norm))
    t_words = set(re.findall(r'\w+', t_norm))
    # Ưu tiên các từ có độ dài trên 2 ký tự (tránh các từ như 'là', 'và', 'the')
    meaningful_q = {w for w in q_words if len(w) > 2}
    meaningful_t = {w for w in t_words if len(w) > 2}
    return len(meaningful_q & meaningful_t) > 0

# --- WIKIPEDIA CORE ---
GLOBAL_WIKI_LOCK = threading.Lock()
LAST_WIKI_REQUEST_TIME = 0.0

def _get_session():
    session = requests.Session()
    # Remove 429 from urllib3 retry so our manual exponential backoff loop handles it with proper Jitter!
    retry = Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504], respect_retry_after_header=True)
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "AntigravityBot/1.2 (https://github.com/phanvantho95/tu_dong_giao_trinh; phanvantho@example.com) Academic Curriculum Builder"})
    return session

def _rate_limit_wiki():
    global LAST_WIKI_REQUEST_TIME
    with GLOBAL_WIKI_LOCK:
        import time
        now = time.time()
        elapsed = now - LAST_WIKI_REQUEST_TIME
        if elapsed < 1.0: # Max 1 request per second globally to avoid 429
            time.sleep(1.0 - elapsed)
        LAST_WIKI_REQUEST_TIME = time.time()

def _api(lang: str) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"

def _page_url(lang: str, title: str) -> str:
    return f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"

@lru_cache(maxsize=100)
def tim_kiem_tieu_de(lang: str, tu_khoa: str, gioi_han: int = 3):
    session = _get_session()
    for attempt in range(5):
        try:
            _rate_limit_wiki()
            r = session.get(_api(lang), params={"action": "query", "list": "search", "srsearch": tu_khoa, "srlimit": gioi_han, "format": "json"}, timeout=45, verify=False)
            r.raise_for_status() # Raise Exception on 429
            return [it["title"] for it in r.json().get("query", {}).get("search", [])]
        except Exception as e:
            if attempt == 4:
                logger.error(f"[WIKI API] tim_kiem_tieu_de failed for '{tu_khoa}' after 5 attempts: {e}")
            
            # Exponential backoff with jitter
            sleep_time = (2 ** attempt) + random.uniform(0.5, 1.5)
            if "429" in str(e):
                logger.warning(f"[WIKI API] 429 Too Many Requests. Sleeping {sleep_time:.2f}s...")
            time.sleep(sleep_time)
    return []

def extract_tables_and_refs(lang: str, title: str) -> str:
    """Trích xuất Bảng biểu và Nguồn tham khảo từ HTML của Wiki và chuyển thành Markdown"""
    session = _get_session()
    try:
        r = session.get(_api(lang), params={
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json"
        }, timeout=15, verify=False)
        r.raise_for_status()
        html = r.json().get("parse", {}).get("text", {}).get("*", "")
        if not html: return ""
        
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return ""
            
        soup = BeautifulSoup(html, "html.parser")
        extra_md = []
        
        # 1. Trích xuất Bảng biểu (Giới hạn top 3 bảng để tiết kiệm token)
        tables = soup.find_all("table", class_=["wikitable", "infobox"])
        for tbl in tables[:3]:
            rows = tbl.find_all("tr")
            if not rows: continue
            md = ""
            for i, row in enumerate(rows[:15]): # Max 15 rows per table
                cells = row.find_all(["th", "td"])
                if not cells: continue
                md += "| " + " | ".join(c.get_text(separator=" ", strip=True).replace("|", "\\|") for c in cells) + " |\n"
                if i == 0:
                    md += "|" + "|".join("---" for _ in cells) + "|\n"
            if md: extra_md.append(md)
            
        # 2. Trích xuất Nguồn tham khảo (Giới hạn top 10 nguồn)
        refs = soup.find_all("ol", class_="references")
        if refs:
            ref_items = refs[0].find_all("li", limit=10)
            ref_texts = ["- " + item.get_text(separator=" ", strip=True) for item in ref_items]
            if ref_texts:
                extra_md.append("### Nguồn tham khảo gốc:\n" + "\n".join(ref_texts))
                
        return "\n\n".join(extra_md)
    except Exception as e:
        logger.warning(f"[WIKI API] extract_tables_and_refs failed for '{title}': {e}")
        return ""

def lay_noi_dung_va_lien_ket(lang: str, title: str, max_links: int = 50):
    cache_key = f"{lang}:{title}"
    with WIKI_LOCK:
        if cache_key in WIKI_CACHE:
            return WIKI_CACHE[cache_key]

    session = _get_session()
    for attempt in range(5):
        try:
            _rate_limit_wiki()
            r = session.get(_api(lang), params={"action": "query", "prop": "extracts|links", "titles": title, "explaintext": 1, "redirects": 1, "plnamespace": 0, "pllimit": max_links, "format": "json"}, timeout=45, verify=False)
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            if "missing" in page:
                # V29: Wikipedia Title Auto-Correction
                search_results = tim_kiem_tieu_de(lang, title, gioi_han=1)
                if search_results:
                    corrected_title = search_results[0]
                    if corrected_title.lower() != title.lower():
                        logger.info(f"[WIKI] Auto-corrected title '{title}' -> '{corrected_title}'")
                        return lay_noi_dung_va_lien_ket(lang, corrected_title, max_links)
                return "", [], ""
                
            extract_text = page.get("extract", "")
            # V40: Bổ sung Bảng biểu và Nguồn tham khảo (Wiki-only Constraint)
            extra_data = extract_tables_and_refs(lang, page.get("title", title))
            if extra_data:
                extract_text += "\n\n" + extra_data
                
            res = extract_text, [l.get("title") for l in page.get("links", []) if l.get("title")], _page_url(lang, page.get("title", title))
            
            with WIKI_LOCK:
                WIKI_CACHE[cache_key] = res
            return res
        except Exception as e:
            if attempt == 4:
                logger.error(f"[WIKI API] lay_noi_dung_va_lien_ket failed for '{title}' after 5 attempts: {e}")
            sleep_time = (2 ** attempt) + random.uniform(0.5, 1.5)
            if "429" in str(e):
                logger.warning(f"[WIKI API] 429 Too Many Requests. Sleeping {sleep_time:.2f}s...")
            time.sleep(sleep_time)
    return "", [], ""

def extract_truth_seed(lang: str, title: str, intro: str, api_key: str, original_topic: str = None, search_model: str = None) -> dict:
    """V27: Trích xuất Truth Seed (Category bằng API + Alias bằng LLM) để neo Entity."""
    cache_key = f"{lang}:{title}"
    with SEED_LOCK:
        if cache_key in SEED_CACHE:
            return SEED_CACHE[cache_key]

    seed = {
        "entity_name": title,
        "aliases": [title, title.lower(), remove_diacritics(title).lower()],
        "best_en_alias": None,
        "categories": []
    }

    # 1. API: Lấy categories (Deterministic)
    session = _get_session()
    try:
        r = session.get(_api(lang), params={
            "action": "query", "prop": "categories", "titles": title, 
            "clshow": "!hidden", "cllimit": 20, "format": "json"
        }, timeout=15, verify=False)
        pages = r.json().get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        if "categories" in page:
            for c in page["categories"]:
                cat_title = c.get("title", "").replace("Thể loại:", "").replace("Category:", "").strip()
                if cat_title:
                    seed["categories"].append(cat_title)
    except Exception as e:
        logger.error(f"[Truth Seed] Error fetching categories: {e}")

    if intro and api_key:
        target_entity = original_topic if original_topic else title
        prompt = f"""Extract aliases, alternative names, acronyms, or common English names for the specific entity "{target_entity}" based on the context of the text below.
Return ONLY a JSON object with two fields:
1. "aliases": array of strings. Example: ["Alias 1", "Alias 2"].
2. "best_en_alias": the most accurate English translation for "{target_entity}" (or null if none exists). 
CRITICAL: If the text describes a broader topic (e.g. "{title}"), you MUST ensure the translation specifically matches "{target_entity}" (e.g., "Information technology law" for "Luật công nghệ thông tin"), NOT the broader topic.
TEXT: {intro[:1000]}"""
        try:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=search_model or CauHinh.SEARCH_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content
            parsed = safe_parse_json(content)
            if parsed and isinstance(parsed, dict):
                aliases = parsed.get("aliases", [])
                best_en = parsed.get("best_en_alias")
                if best_en and isinstance(best_en, str):
                    seed["best_en_alias"] = best_en
                    aliases.append(best_en)
            else:
                # Fallback list parsing
                import ast
                start = content.find('[')
                end = content.rfind(']') + 1
                if start != -1 and end != -1:
                    aliases = ast.literal_eval(content[start:end])
                else:
                    aliases = []
                    
            if isinstance(aliases, list):
                for a in aliases:
                    if isinstance(a, str) and a not in seed["aliases"]:
                        seed["aliases"].extend([a, a.lower(), remove_diacritics(a).lower()])
        except Exception as e:
            logger.error(f"[Truth Seed] LLM Alias Error: {e}")

    # Auto Alias Expansion cho địa danh
    lower_t = title.lower()
    if "tỉnh" in lower_t and not lower_t.startswith("tỉnh"):
        seed["aliases"].extend([f"Tỉnh {title}", f"tinh {remove_diacritics(title).lower()}"])
    if "thành phố" in lower_t and not lower_t.startswith("thành phố"):
        seed["aliases"].extend([f"Thành phố {title}", f"thanh pho {remove_diacritics(title).lower()}"])
        
    # Xóa trùng lặp
    seed["aliases"] = list(set(seed["aliases"]))
    
    with SEED_LOCK:
        SEED_CACHE[cache_key] = seed
        
    logger.info(f"[Truth Seed] Anchored '{title}': {len(seed['aliases'])} aliases, {len(seed['categories'])} categories.")
    return seed

# --- ADAPTIVE ENGINES (V17.1) ---
def semantic_query_deduplicate(queries: list, api_key: str, threshold: float = 0.9):
    """Loại bỏ các truy vấn trùng lặp ngữ nghĩa cao (> 0.9) để tiết kiệm tài nguyên."""
    if not queries or len(queries) < 2: return queries
    from google import genai
    import numpy as np
    from cau_hinh import CauHinh
    
    # Batch embed queries
    q_texts = [q["title"] for q in queries]
    model_name = getattr(CauHinh, "GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
    vectors = None
    
    try:
        from dich_vu.embedding_pool import embedding_pool
        res = embedding_pool.embed_content(texts=q_texts, model_name=model_name)
        if res:
            v_list = []
            for vec in res:
                v = np.array(vec)
                v_list.append(v / np.linalg.norm(v))
            vectors = v_list
    except Exception as ex:
        import logging
        logging.getLogger(__name__).warning(f"[Deduplicate] Embedding pool failed: {ex}")
            
    if not vectors:
        import logging
        logging.getLogger(__name__).error("[Deduplicate] All Gemini keys failed for embedding.")
        return queries
    
    keep_indices = []
    for i, v in enumerate(vectors):
        is_duplicate = False
        for prev_idx in keep_indices:
            sim = np.dot(v, vectors[prev_idx])
            if sim > threshold:
                is_duplicate = True; break
        if not is_duplicate:
            keep_indices.append(i)
    return [queries[i] for i in keep_indices]

# --- MULTI-AGENT DISCOVERY (Planner -> Searcher -> Critic) ---

def agent_curriculum_planner(topic: str, quy_mo: str, api_key: str, search_model: str = None) -> list:
    """AGENT 1: The Curriculum Planner (Vạch ra Bản đồ tri thức)
    V41: Sinh pillars kèm wiki_suggestions để Search Specialist có thể tìm chính xác hơn.
    """
    client = OpenAI(api_key=api_key)
    count = {"can_ban": 3, "tieu_chuan": 5, "chuyen_sau": 8}.get(quy_mo, 5)
    
    prompt = f"""You are an Academic Curriculum Architect planning a university-level textbook about '{topic}'.

Your task: Identify exactly {count} CORE KNOWLEDGE AREAS that a standard university textbook on '{topic}' MUST cover.

CRITICAL RULES:
1. Each pillar must be a SPECIFIC, TECHNICAL sub-domain — NOT a vague category.
   BAD examples: "Security and Management" (too broad), "Applications and Society" (too vague)
   GOOD examples: "Cryptographic Protocols and Network Security", "Transport Layer Protocols (TCP/UDP)"
2. Pillars must follow standard university curriculum progression for this field.
3. For each pillar, suggest exactly 3 Wikipedia article titles (in the SAME language as '{topic}') that would contain authoritative academic content for that pillar. These should be real, specific encyclopedia article names — not chapter titles.
4. Do NOT include tangential topics like social media platforms, pop culture, entertainment, or general news unless they are technically core to '{topic}'.
5. Cover the full depth of the discipline: from foundational theory to advanced applications.

Return MUST be JSON:
{{"pillars": [
  {{"name": "Pillar Name", "wiki_suggestions": ["Article Title 1", "Article Title 2", "Article Title 3"]}}
]}}"""
    
    try:
        resp = client.chat.completions.create(
            model=search_model or CauHinh.SEARCH_MODEL, 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        data = json.loads(resp.choices[0].message.content)
        raw_pillars = data.get("pillars", [])
        clean_pillars = []
        for p in raw_pillars:
            if isinstance(p, dict):
                name = p.get("name", p.get("title", str(p)))
                wiki_hints = p.get("wiki_suggestions", p.get("wiki_hints", []))
                if not isinstance(wiki_hints, list):
                    wiki_hints = []
                clean_pillars.append({"name": name, "wiki_hints": wiki_hints[:3]})
            else:
                clean_pillars.append({"name": str(p), "wiki_hints": []})
        return clean_pillars
    except Exception as e:
        logger.error(f"[Planner Agent] Error: {e}")
        return [{"name": "Tổng quan", "wiki_hints": []}, {"name": "Lịch sử hình thành", "wiki_hints": []}, {"name": "Đặc điểm cơ bản", "wiki_hints": []}]

def agent_search_specialist(topic: str, pillars: list, api_key: str, truth_seed: dict = None, ngon_ngu: str = "vi", search_model: str = None) -> list:
    """AGENT 2: The Search Specialist (3-Tier Wikipedia Retrieval)
    V41: Fallback 3 tầng — Wiki Hints → AI Keywords → Cross-lingual fallback.
    V44: Language-aware — ưu tiên ngôn ngữ theo lựa chọn user.
    """
    client = OpenAI(api_key=api_key)
    queries = []
    
    # V44: Xác định ngôn ngữ chính và ngôn ngữ fallback
    primary_lang = "en" if ngon_ngu == "en" else "vi"
    fallback_lang = "vi" if ngon_ngu == "en" else "en"
    
    seed_context = ""
    if truth_seed:
        seed_context = f"\nContext/Core Entity: {truth_seed.get('entity_name', topic)}\nAliases: {truth_seed.get('aliases', [])}\nCategories: {truth_seed.get('categories', [])}\n"
    
    for p in pillars:
        if isinstance(p, dict):
            pillar_name = p.get("name", str(p))
            wiki_hints = p.get("wiki_hints", [])
        else:
            pillar_name = str(p)
            wiki_hints = []
        
        found_for_pillar = False
        
        # ═══ TIER 1: Thử wiki_hints từ Planner ═══
        for hint in wiki_hints:
            if not hint or not isinstance(hint, str):
                continue
            res = tim_kiem_tieu_de(primary_lang, hint.strip(), gioi_han=3)
            for title in res:
                if not truth_seed or is_title_relevant(truth_seed, title, query=hint, search_topic=topic):
                    queries.append({"title": title, "lang": primary_lang, "reason": pillar_name})
                    found_for_pillar = True
                    logger.info(f"[Search Agent] TIER-1 HIT: '{hint}' → '{title}' (pillar: {pillar_name})")
                    break
            if found_for_pillar:
                break
        
        if found_for_pillar:
            continue
        
        # ═══ TIER 2: AI sinh keyword ═══
        try:
            prompt = f"""You are a Wikipedia Search Specialist.
Topic: {topic}{seed_context}
Sub-topic (Pillar): {pillar_name}
Generate EXACTLY 3 highly probable Wikipedia article titles in {'ENGLISH' if primary_lang == 'en' else 'the SAME LANGUAGE as the topic'} '{topic}'.
These must be REAL encyclopedia article names, not chapter titles or textbook headings.
CRITICAL RULE: The suggested articles MUST be strictly related to the main Topic ('{topic}'). Do NOT generate generic words, country names, social media platforms, or unrelated concepts.
Return MUST be JSON: {{"keywords": ["keyword 1", "keyword 2", "keyword 3"]}}"""
            resp = client.chat.completions.create(
                model=search_model or CauHinh.SEARCH_MODEL, 
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            kw = json.loads(resp.choices[0].message.content).get("keywords", [])
            
            for k in kw:
                res = tim_kiem_tieu_de(primary_lang, k, gioi_han=3)
                for title in res:
                    if not truth_seed or is_title_relevant(truth_seed, title, query=k, search_topic=topic):
                        queries.append({"title": title, "lang": primary_lang, "reason": pillar_name})
                        found_for_pillar = True
                        logger.info(f"[Search Agent] TIER-2 HIT: '{k}' → '{title}' (pillar: {pillar_name})")
                        break
                if found_for_pillar:
                    break
        except Exception as e:
            logger.error(f"[Search Agent] TIER-2 Error on pillar '{pillar_name}': {e}")
        
        # Fallback tìm chính tên pillar
        if not found_for_pillar:
            res = tim_kiem_tieu_de(primary_lang, pillar_name, gioi_han=3)
            for title in res:
                if not truth_seed or is_title_relevant(truth_seed, title, query=pillar_name, search_topic=topic):
                    queries.append({"title": title, "lang": primary_lang, "reason": pillar_name})
                    found_for_pillar = True
                    logger.info(f"[Search Agent] TIER-2 FALLBACK: '{pillar_name}' → '{title}'")
                    break
        
        # ═══ TIER 3: Cross-lingual fallback ═══
        if not found_for_pillar:
            fl_res = tim_kiem_tieu_de(fallback_lang, pillar_name, gioi_han=3)
            for title in fl_res:
                if not truth_seed or is_title_relevant(truth_seed, title, query=pillar_name, search_topic=topic):
                    queries.append({"title": title, "lang": fallback_lang, "reason": pillar_name})
                    logger.info(f"[Search Agent] TIER-3 {fallback_lang.upper()}: '{pillar_name}' → '{title}'")
                    found_for_pillar = True
                    break
            if not found_for_pillar:
                logger.warning(f"[Search Agent] ALL TIERS FAILED for pillar: '{pillar_name}'")
            
    return queries

def agent_knowledge_critic(topic: str, pillars: list, found_queries: list, api_key: str, search_model: str = None) -> list:
    """AGENT 3: The Knowledge Critic (Kiểm toán rỗng)
    V41: Hỗ trợ pillars dạng dict.
    """
    client = OpenAI(api_key=api_key) # Dùng OpenAI cho nhanh và ổn định JSON
    found_reasons = [q["reason"] for q in found_queries]
    
    # V41: Extract pillar names từ dict format
    pillar_names = []
    for p in pillars:
        if isinstance(p, dict):
            pillar_names.append(p.get("name", str(p)))
        else:
            pillar_names.append(str(p))
    
    prompt = f"""You are a Knowledge Critic.
Topic: {topic}
Required Pillars: {pillar_names}
Successfully Retrieved Pillars: {found_reasons}

List any Required Pillars that are COMPLETELY MISSING from the retrieved list.
Return MUST be JSON: {{"missing_pillars": ["...", "..."]}}"""
    try:
        resp = client.chat.completions.create(
            model=search_model or CauHinh.SEARCH_MODEL, 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        data = json.loads(resp.choices[0].message.content)
        return data.get("missing_pillars", [])
    except Exception as e:
        logger.error(f"[Critic Agent] Error: {e}")
        return []

def agent_link_curator(topic: str, raw_links: list, api_key: str, max_links: int = 15, truth_seed: dict = None, search_model: str = None) -> list:
    """
    AGENT 4 (V9 Upgraded): The Link Curator - Hybrid LLM Spidering
    Sử dụng BM25 để lọc thô, sau đó gọi OpenAI LLM để chọn lọc tinh các liên kết sâu.
    """
    if not raw_links: return []
    
    unique_links = list(set(raw_links))
    
    # 1. Khởi tạo BM25 Lite
    from .lam_sach_van_ban import remove_diacritics
    import math
    from collections import Counter
    import re
    
    def _tokenize_vi(text: str) -> list:
        t = remove_diacritics(text).lower()
        return [w for w in re.findall(r'\w+', t) if len(w) > 2]
    
    query_tokens = _tokenize_vi(topic)
    doc_tokens_list = [_tokenize_vi(link) for link in unique_links]
    
    N = len(doc_tokens_list)
    df = Counter()
    for tokens in doc_tokens_list:
        for t in set(tokens):
            df[t] += 1
            
    idf = {}
    for t in query_tokens:
        idf[t] = math.log(1 + (N - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5))
        
    avgdl = sum(len(t) for t in doc_tokens_list) / max(1, N)
    
    # Truth Seed aliases
    seed_aliases = []
    if truth_seed and "aliases" in truth_seed:
        seed_aliases = [remove_diacritics(a).lower() for a in truth_seed["aliases"]]
        
    scored_links = []
    for i, link in enumerate(unique_links):
        tokens = doc_tokens_list[i]
        link_lower_norm = remove_diacritics(link).lower()
        
        # A. Tính điểm BM25
        dl = len(tokens)
        bm25_score = 0.0
        tf = Counter(tokens)
        for t in query_tokens:
            if t in tf:
                freq = tf[t]
                bm25_score += idf[t] * (freq * 2.5) / (freq + 1.5 * (0.25 + 0.75 * dl / avgdl))
                
        # B. Tính điểm Entity Overlap
        overlap_score = 0.0
        if seed_aliases:
            if any(a in link_lower_norm for a in seed_aliases):
                overlap_score = 5.0  # Boost mạnh nếu chứa entity chính
                
        # C. Category/Broad page penalty
        penalty = 0.0
        broad_terms = ["việt nam", "hoa kỳ", "thế giới", "châu á", "lịch sử", "địa lý", "quốc gia", "tỉnh", "thành phố", "danh sách"]
        if any(link_lower_norm == b for b in broad_terms):
            penalty = 10.0 # Trừ điểm các trang quá rộng nếu nó chỉ là 1 chữ
            
        total_score = bm25_score + overlap_score - penalty
        scored_links.append((total_score, link))
        
    # Lấy top 40 từ BM25 để gửi cho LLM (Hybrid approach)
    top_candidates = [link for score, link in scored_links if score > -5][:40]
    
    if not top_candidates or not api_key:
        return top_candidates[:max_links]
        
    # Gọi LLM để chọn tinh
    from openai import OpenAI
    import json
    from cau_hinh import CauHinh
    client = OpenAI(api_key=api_key)
    
    prompt = f"""You are an Expert Knowledge Spider for the topic '{topic}'.
Your task is to select up to {max_links} MOST VALUABLE Wikipedia article links from the candidate list below.
Choose links that provide deep, academic, or crucial supplementary knowledge related to '{topic}'.

CANDIDATE LINKS:
{json.dumps(top_candidates, ensure_ascii=False)}

Return JSON exactly like this:
{{"selected_links": ["Link 1", "Link 2"]}}
"""
    try:
        resp = client.chat.completions.create(
            model=search_model or CauHinh.SEARCH_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        selected = data.get("selected_links", [])
        # Ensure we only return valid candidate links
        final_links = [link for link in selected if link in top_candidates][:max_links]
        return final_links if final_links else top_candidates[:max_links]
    except Exception as e:
        logger.warning(f"[Link Curator] LLM Spidering failed: {e}. Falling back to BM25.")
        return top_candidates[:max_links]

def multi_agent_identify_wiki_titles(topic: str, quy_mo: str = "tieu_chuan", api_key: str = None, is_expansion: bool = False, truth_seed: dict = None, ngon_ngu: str = "vi", search_model: str = None, **kwargs):
    """
    Orchestrator: Planner -> Searcher -> Critic Loop
    V44: Language-aware Wikipedia retrieval.
    """
    if not api_key: return []
    
    primary_lang = "en" if ngon_ngu == "en" else "vi"
    
    logger.info(f"[MULTI-AGENT] 🗺️ Planner is mapping knowledge pillars for '{topic}'...")
    pillars = agent_curriculum_planner(topic, quy_mo, api_key, search_model=search_model)
    pillar_display = [p["name"] if isinstance(p, dict) else p for p in pillars]
    logger.info(f"[MULTI-AGENT] Target Pillars: {pillar_display}")
    
    logger.info(f"[MULTI-AGENT] 🔎 Search Specialist is hunting {len(pillars)} pillars on Wikipedia ({primary_lang})...")
    queries = agent_search_specialist(topic, pillars, api_key, truth_seed, ngon_ngu=ngon_ngu, search_model=search_model)
    
    # Critic Audit (Vòng lặp)
    logger.info(f"[MULTI-AGENT] 🧐 Knowledge Critic is auditing coverage...")
    missing = agent_knowledge_critic(topic, pillars, queries, api_key, search_model=search_model)
    
    if missing:
        logger.warning(f"[MULTI-AGENT] ⚠️ Critic found missing pillars: {missing}. Dispatching Searcher again...")
        refined_missing = [f"{topic} {m}" for m in missing]
        extra_queries = agent_search_specialist(topic, refined_missing, api_key, truth_seed, ngon_ngu=ngon_ngu, search_model=search_model)
        queries.extend(extra_queries)
        logger.info(f"[MULTI-AGENT] Recovered {len(extra_queries)} additional sources.")
    else:
        logger.info(f"[MULTI-AGENT] ✅ Critic approved 100% coverage.")
        
    # Deduplicate
    final_queries = semantic_query_deduplicate(queries, api_key)
    
    # CRITICAL: Always ensure the truth_seed entity is in the final list
    if truth_seed and truth_seed.get("entity_name"):
        entity = truth_seed.get("entity_name")
        if not any(q.get("title", "").lower() == entity.lower() for q in final_queries):
            final_queries.insert(0, {"title": entity, "lang": primary_lang, "reason": "Truth Seed Anchor"})
            
    logger.info(f"[MULTI-AGENT] Final Deduplicated Queries: {[q['title'] for q in final_queries]}")
    return final_queries


# V41: Noise title patterns — các bài Wikipedia phổ thông hay gây nhiễu
# CHỈ bị chặn khi title KHÔNG liên quan đến cả search_topic LẪN query (pillar)
_NOISE_TITLE_PATTERNS = {
    "facebook", "twitter", "instagram", "tiktok", "youtube", "google", "apple",
    "amazon", "microsoft", "netflix", "snapchat", "whatsapp", "telegram",
    "danh sách danh sách", "thẩm mỹ y2k",
}

def _is_noise_title(title: str, search_topic: str, query: str = "") -> bool:
    """V41: Phát hiện bài viết phổ thông/giải trí gây nhiễu.
    An toàn đa lĩnh vực: Chỉ block nếu title KHÔNG liên quan đến 
    CẢ search_topic LẪN query (pillar đang tìm kiếm).
    
    Ví dụ:
    - Topic "Mạng Máy Tính", query "Bảo mật" → "Facebook" BỊ CHẶN ✓
    - Topic "Marketing Số", query "Social Media Marketing" → "Facebook" KHÔNG BỊ CHẶN ✓
    - Topic "Facebook", query bất kỳ → "Facebook" KHÔNG BỊ CHẶN ✓
    """
    t_lower = title.lower().strip()
    
    # Không nằm trong danh sách noise → không block
    if t_lower not in _NOISE_TITLE_PATTERNS:
        return False
    
    # Kiểm tra liên quan đến search_topic
    topic_lower = search_topic.lower().strip() if search_topic else ""
    if topic_lower and (t_lower in topic_lower or topic_lower in t_lower):
        return False  # Topic chính liên quan → không block
    
    # Kiểm tra liên quan đến query/pillar (AN TOÀN ĐA LĨNH VỰC)
    if query:
        q_lower = query.lower().strip()
        q_norm = remove_diacritics(query).lower().strip()
        if t_lower in q_lower or t_lower in q_norm:
            return False  # Pillar đang tìm kiếm liên quan → không block
        # Kiểm tra từ khóa liên quan (ví dụ: "social media" chứa context cho "facebook")
        social_context = {"social", "media", "marketing", "truyền thông", "mạng xã hội", 
                         "quảng cáo", "digital", "thương mại điện tử", "e-commerce",
                         "advertising", "platform", "nền tảng"}
        q_words = set(q_lower.split()) | set(q_norm.split())
        if q_words & social_context:
            return False  # Query có ngữ cảnh liên quan → không block
    
    return True

def is_title_relevant(truth_seed: dict, title: str, query: str = "", search_topic: str = "") -> bool:
    """Kiểm tra title có chứa bất kỳ alias nào của Truth Seed hay query/topic hay không.
    V41: Thêm noise detection + nâng ngưỡng overlap để chống pha loãng.
    """
    t_norm = remove_diacritics(title).lower()
    t_raw_lower = title.lower()
    
    # V41: Noise Gate — chặn bài viết phổ thông/giải trí (context-aware)
    if _is_noise_title(title, search_topic, query):
        logger.debug(f"[Relevance] Noise blocked: '{title}' (topic={search_topic}, query={query})")
        return False
    
    # 1. Check against explicitly generated query and original topic
    for q in [query, search_topic]:
        if q:
            q_norm = remove_diacritics(q).lower()
            if q_norm in t_norm or t_norm in q_norm:
                return True
            q_words = set(w for w in re.findall(r'\w+', q_norm) if len(w) > 2)
            t_words = set(w for w in re.findall(r'\w+', t_norm) if len(w) > 2)
            if q_words and len(q_words & t_words) / max(1, len(q_words)) >= 0.5:
                return True
                
    # 2. Check against Truth Seed aliases
    for a in truth_seed.get("aliases", []):
        if a.lower() in t_raw_lower or a.lower() in t_norm:
            return True
            
    entity_name = truth_seed.get("entity_name", "")
    q_words = set(w for w in re.findall(r'\w+', remove_diacritics(entity_name).lower()) if len(w) > 2)
    t_words = set(w for w in re.findall(r'\w+', t_norm) if len(w) > 2)
    
    if not q_words: return False
    
    overlap_ratio = len(q_words & t_words) / max(1, len(q_words))
    
    # V41: Nâng ngưỡng overlap để siết chất lượng
    if len(q_words) <= 2:
        if overlap_ratio >= 0.6: return True
    else:
        if overlap_ratio >= 0.5: return True
        
    # Categories fallback (Level 2 relaxation)
    for cat in truth_seed.get("categories", []):
        cat_words = set(w for w in re.findall(r'\w+', remove_diacritics(cat).lower()) if len(w) > 2)
        if len(cat_words & t_words) > 0:
            return True
            
    return False

# --- ADAPTIVE KNOWLEDGE RETRIEVAL ENGINE (EKRE-V27 DIAMOND) ---
def ekre_discovery_engine(topic: str, api_keys_list: list, quy_mo: str = "tieu_chuan", api_key_openai: str = None, original_topic: str = None, chapter_hints: list = None, ngon_ngu: str = "vi", search_model: str = None):
    from .vector_search import hybrid_semantic_filter, deduplicate_by_embedding, ensure_topic_diversity, coverage_aware_ranking
    from .lam_sach_van_ban import chia_doan, lam_sach_trang
    
    search_topic = original_topic or topic
    
    # Map search topics that are known to not exist on Wikipedia to existing equivalent topics (V44.2)
    TOPIC_SEARCH_MAPPING = {
        "lập trình di động": "Ứng dụng di động",
        "lap trinh di dong": "Ứng dụng di động",
        "quản lý dự án công nghệ thông tin": "Quản lý dự án phần mềm",
        "quan ly du an cong nghe thong tin": "Quản lý dự án phần mềm",
        "an toàn và bảo mật thông tin": "An toàn thông tin",
        "an toan va bao mat thong tin": "An toàn thông tin",
        "công nghệ chuỗi khối": "Blockchain",
        "cong nghe chuoi khoi": "Blockchain",
        "lập trình wpf": "Windows Presentation Foundation",
        "lap trinh wpf": "Windows Presentation Foundation",
        "khởi nghiệp và đổi mới sáng tạo": "Khởi nghiệp",
        "khoi nghiep va doi moi sang tao": "Khởi nghiệp",
        # Programming specific mappings to prevent topic drift/character conflicts
        "c#": "C Sharp (ngôn ngữ lập trình)",
        "c sharp": "C Sharp (ngôn ngữ lập trình)",
        "lập trình c#": "C Sharp (ngôn ngữ lập trình)",
        "ngôn ngữ c#": "C Sharp (ngôn ngữ lập trình)",
        "c++": "C++",
        "lập trình c++": "C++",
        "ngôn ngữ c++": "C++",
        "swift": "Swift (ngôn ngữ lập trình)",
        "lập trình swift": "Swift (ngôn ngữ lập trình)",
        "ngôn ngữ swift": "Swift (ngôn ngữ lập trình)",
        "golang": "Go (ngôn ngữ lập trình)",
        "go": "Go (ngôn ngữ lập trình)",
        "lập trình golang": "Go (ngôn ngữ lập trình)",
        "python": "Python (ngôn ngữ lập trình)",
        "lập trình python": "Python (ngôn ngữ lập trình)",
        "ngôn ngữ python": "Python (ngôn ngữ lập trình)",
        "rust": "Rust (ngôn ngữ lập trình)",
        "lập trình rust": "Rust (ngôn ngữ lập trình)",
        "ngôn ngữ rust": "Rust (ngôn ngữ lập trình)",
        "kotlin": "Kotlin (ngôn ngữ lập trình)",
        "lập trình kotlin": "Kotlin (ngôn ngữ lập trình)",
        "ngôn ngữ kotlin": "Kotlin (ngôn ngữ lập trình)"
    }
    mapped_topic = TOPIC_SEARCH_MAPPING.get(search_topic.lower().strip())
    if mapped_topic:
        logger.info(f"[Topic Mapping] Mapping Wikipedia search topic '{search_topic}' -> '{mapped_topic}'")
        search_topic = mapped_topic
    
    # V44: Language-aware discovery
    primary_lang = "en" if ngon_ngu == "en" else "vi"
    fallback_lang = "vi" if ngon_ngu == "en" else "en"
    
    # V44.1: Auto-translate topic when language mismatch detected
    # (User nhập tiếng Việt nhưng chọn English → dịch topic sang English để tìm trên en.wikipedia)
    if primary_lang == "en" and api_key_openai:
        import re as _re
        # Heuristic: nếu topic chứa ký tự có dấu tiếng Việt → cần dịch
        if _re.search(r'[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]', search_topic.lower()):
            try:
                _client = OpenAI(api_key=api_key_openai, max_retries=0)
                _resp = _client.chat.completions.create(
                    model=search_model or CauHinh.SEARCH_MODEL,
                    messages=[{"role": "user", "content": f"Translate this Vietnamese academic topic to English. Return ONLY the English translation, nothing else:\n\n{search_topic}"}],
                    temperature=0.0,
                    max_tokens=100,
                    timeout=10.0
                )
                en_topic = _resp.choices[0].message.content.strip().strip('"').strip("'")
                if en_topic and len(en_topic) > 2:
                    logger.info(f"[V44-Translate] Topic translated: '{search_topic}' → '{en_topic}'")
                    search_topic = en_topic
            except Exception as e:
                logger.warning(f"[V44-Translate] Translation failed: {e}. Using original topic.")
    
    # Diamond X-Ray Stats
    xray = {
        "step": "Discovery",
        "topic": topic,
        "search_topic": search_topic,
        "expanded_queries": [],
        "stats": {"retrieved": 0, "filtered": 0, "final": 0},
        "rejection_reasons": {"disambiguation": 0, "low_relevance": 0, "duplicate": 0}
    }

    logger.info(f"[EKRE-V27] Starting Diamond Discovery: {search_topic} (framed as: {topic}, lang: {primary_lang})")
    
    # --- STAGE 1: Exact Match & Truth Seed Anchoring ---
    exact_titles = tim_kiem_tieu_de(primary_lang, search_topic, gioi_han=1)
    main_entity = exact_titles[0] if exact_titles else search_topic
    
    content, links, url = lay_noi_dung_va_lien_ket(primary_lang, main_entity)
    intro = content[:1000] if content else ""
    truth_seed = extract_truth_seed(primary_lang, main_entity, intro, api_key_openai, original_topic=search_topic, search_model=search_model)
    
    all_raw_docs = []
    seen_titles = set()
    all_internal_links = []
    stats_lock = threading.Lock()
    
    if content and not hard_rule_filter(main_entity, content):
        all_raw_docs.append({
            "title": main_entity, 
            "text": content, 
            "intro": intro,
            "url": url, 
            "lang": primary_lang, 
            "subtopic": "Core Entity", 
            "id": str(uuid.uuid4())[:8],
            "is_core": True,
            "categories": truth_seed.get("categories", [])
        })
        seen_titles.add(main_entity.lower())
        if links: all_internal_links.extend(links)
        
    # --- STAGE 2: Semantic Expansion (Guided) ---
    if chapter_hints and isinstance(chapter_hints, list) and len(chapter_hints) > 0:
        # V37.2: Custom chapters → Tìm kiếm trực tiếp theo tên chương (skip AI Planner)
        ai_titles = []
        ai_titles.append({"title": search_topic, "lang": primary_lang, "reason": f"Main topic: {search_topic}"})
        for ch_name in chapter_hints:
            ch_name = ch_name.strip()
            if ch_name:
                ai_titles.append({"title": ch_name, "lang": primary_lang, "reason": f"Custom chapter: {ch_name}"})
                ai_titles.append({"title": f"{search_topic} {ch_name}", "lang": primary_lang, "reason": f"Topic+Chapter: {ch_name}"})
        logger.info(f"[EKRE-V37] Custom mode: Using main topic '{search_topic}' and {len(chapter_hints)} chapter names as search queries (lang={primary_lang}).")
    else:
        # Auto mode: Dùng AI Planner/Searcher/Critic bình thường
        ai_titles = multi_agent_identify_wiki_titles(search_topic, quy_mo, api_key_openai, truth_seed=truth_seed, ngon_ngu=ngon_ngu, search_model=search_model)
        
        # V40: Category Expansion
        if truth_seed and "categories" in truth_seed:
            for cat in truth_seed["categories"][:2]:
                ai_titles.append({"title": cat, "lang": primary_lang, "reason": "Category Expansion Fallback"})
    
    xray["expanded_queries"] = [q["title"] for q in ai_titles]
    
    def fetch_title(item, sr_limit=5):
        time.sleep(random.uniform(0.2, 0.8)) # Chống Wikipedia API Rate Limit
        query = item["title"]; lang = item["lang"]
        actual_titles = tim_kiem_tieu_de(lang, query, gioi_han=sr_limit) 
        if not actual_titles:
            logger.warning(f"[DEBUG-FETCH] tim_kiem_tieu_de returned empty for query: '{query}'")
            return None
        
        docs = []
        for t in actual_titles:
            lower_t = t.lower()
            with stats_lock:
                xray["stats"]["retrieved"] += 1 
                if lower_t in seen_titles: 
                    xray["rejection_reasons"]["duplicate"] += 1
                    logger.warning(f"[DEBUG-FETCH] '{t}' rejected: Duplicate")
                    continue
                    
                # V27: Title-Level Hard Filter
                if not is_title_relevant(truth_seed, t, query=query, search_topic=search_topic):
                    xray["rejection_reasons"]["low_relevance"] += 1
                    logger.warning(f"[DEBUG-FETCH] '{t}' rejected: Low Relevance (query={query})")
                    continue
                    
                seen_titles.add(lower_t)
                
            content, links, url = lay_noi_dung_va_lien_ket(lang, t)
            if not content:
                logger.warning(f"[DEBUG-FETCH] '{t}' rejected: No content fetched (lay_noi_dung_va_lien_ket returned None)")
                continue
                
            if lang == "en" and primary_lang == "vi" and api_key_openai:
                logger.info(f"[CROSS-LINGUAL] Translating English Wikipedia article '{t}' to Vietnamese...")
                content = dich_tai_lieu_en_sang_vi(content, api_key_openai)
                t = f"{t} (Bản dịch)"
                lang = "vi"
            
            with stats_lock:
                if links:
                    all_internal_links.extend(links)
            
            # Diamond Filter: Disambiguation + Quality
            if hard_rule_filter(t, content): 
                with stats_lock:
                    xray["rejection_reasons"]["disambiguation"] += 1
                logger.warning(f"[DEBUG-FETCH] '{t}' rejected: Hard Rule Filter (disambiguation/too short)")
                continue
            
            # Diamond Intro: Paragraph + First Heading (khoảng 1000 chars)
            intro_limit = 1000
            intro = content[:intro_limit]
            
            docs.append({
                "title": t, 
                "text": content, 
                "intro": intro,
                "url": url, 
                "lang": lang, 
                "subtopic": item.get("reason", "Main"), 
                "id": str(uuid.uuid4())[:8]
            })
            # V21.7: Removed old retrieved increment here to avoid triple-counting
            # (Now moved to top of loop)
        return docs if docs else None

    if ai_titles:
        # V29 Hybrid: Deterministic Backbone — thu thập tất cả trước, trim sau
        # Loại bỏ race condition: thứ tự kết quả theo thứ tự AI titles, không theo thread speed
        sr_initial = 10 if quy_mo == "chuyen_sau" else 5
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda x: fetch_title(x, sr_limit=sr_initial), ai_titles))
        for i, r in enumerate(results):
            if r: all_raw_docs.extend(r)
            if i % 2 == 0: logger.info(f"[FETCH] Discovery Progress: {len(all_raw_docs)} docs collected...")
            if len(all_raw_docs) >= 500: 
                logger.warning(f"[EKRE] Soft Cap reached (500 docs).")
                break

    # --- ADAPTIVE TRIGGER: CROSS-LINGUAL PROGRESSIVE RETRIEVAL ---
    # V35.1: Ngưỡng điều chỉnh theo công thức mới (unique_titles * 15 + chars / 5000)
    target_score = {"can_ban": 60, "tieu_chuan": 120, "chuyen_sau": 250}.get(quy_mo, 120)
    current_score = score_knowledge_base(all_raw_docs)
    
    best_en_alias = truth_seed.get("best_en_alias")
    coverage_low = current_score < (target_score * 0.6)
    
    # Global Topic Heuristic (Science, IT, Global Culture, etc)
    global_keywords = ["ai", "thuật toán", "công nghệ", "sinh học", "vật lý", "văn hóa toàn cầu", "hội chứng"]
    is_global_topic = any(k in search_topic.lower() for k in global_keywords)
    
    # V44: Nếu primary_lang đã là EN, skip cross-lingual trigger (đã crawl EN rồi)
    enable_en = (primary_lang != "en") and (coverage_low or is_global_topic or (best_en_alias is not None)) and (best_en_alias is not None)
    
    if enable_en:
        logger.info(f"[CROSS-LINGUAL] Triggering EN Retrieval for '{best_en_alias}' (Coverage Low: {coverage_low}, Global: {is_global_topic})")
        # Fetch top 3 EN docs using best_en_alias
        en_titles = tim_kiem_tieu_de("en", best_en_alias, gioi_han=3)
        if en_titles:
            for en_t in en_titles:
                en_content, en_links, en_url = lay_noi_dung_va_lien_ket("en", en_t)
                if en_content and not hard_rule_filter(en_t, en_content):
                    if primary_lang == "vi" and api_key_openai:
                        logger.info(f"[CROSS-LINGUAL] Translating progressive English Wikipedia doc '{en_t}' to Vietnamese...")
                        vi_content = dich_tai_lieu_en_sang_vi(en_content, api_key_openai)
                        vi_title = f"{en_t} (Bản dịch)"
                        all_raw_docs.append({
                            "title": vi_title, 
                            "text": vi_content, 
                            "intro": vi_content[:1000],
                            "url": en_url, 
                            "lang": "vi", 
                            "subtopic": "EN Anchor Expansion", 
                            "id": str(uuid.uuid4())[:8],
                            "is_en_anchor": True
                        })
                    else:
                        all_raw_docs.append({
                            "title": en_t, 
                            "text": en_content, 
                            "intro": en_content[:1000],
                            "url": en_url, 
                            "lang": "en", 
                            "subtopic": "EN Anchor Expansion", 
                            "id": str(uuid.uuid4())[:8],
                            "is_en_anchor": True
                        })
                    if en_links: all_internal_links.extend(en_links)
    
    # Update score after potential EN expansion
    current_score = score_knowledge_base(all_raw_docs)

    # =========================================================================
    # EKRE V26.2: ADAPTIVE THRESHOLD & SAFE DEGRADATION
    # =========================================================================

    complexity = detect_topic_complexity(search_topic, api_key_openai, search_model=search_model)
    xray["complexity"] = complexity
    logger.info(f"[EKRE-V26.2] Topic Complexity: {complexity.upper()} | RawDocs: {len(all_raw_docs)}")

    hardened, adaptive_analytics = _apply_adaptive_yield_gate(
        raw_docs=all_raw_docs,
        topic=search_topic,
        api_key_openai=api_key_openai,
        quy_mo=quy_mo,
        complexity=complexity,
        fetch_title_func=fetch_title,
        ai_titles=ai_titles,
        truth_seed=truth_seed
    )
    xray["adaptive"] = adaptive_analytics

    # =========================================================================
    # EKRE V28: MULTI-AGENT CRITIC (Gemini LLM Validator)
    # =========================================================================
    from dich_vu.gemini_da_buoc import gemini_critic_agent
    
    hardened = sorted(hardened, key=lambda x: x.get("relevance_score", 0), reverse=True)
    top_candidates = hardened[:30]
    final_approved = []
    
    logger.info(f"[MULTI-AGENT] Sending {len(top_candidates)} top candidates to Critic Agent (Gemini)...")
    
    # V36.4: Truyền aliases từ Truth Seed để Critic nhận diện tên gọi khác
    critic_aliases = truth_seed.get("aliases", []) if truth_seed else []
    # Thêm entity_name (tên chính trên Wikipedia) vào danh sách aliases
    if truth_seed and truth_seed.get("entity_name"):
        entity = truth_seed["entity_name"]
        if entity not in critic_aliases:
            critic_aliases = [entity] + critic_aliases
    
    def _run_critic(doc):
        res = gemini_critic_agent(search_topic, doc.get("title", ""), doc.get("text", ""), api_keys_list, aliases=critic_aliases)
        doc["critic_approved"] = res.get("is_approved", False)
        doc["critic_reason"] = res.get("reason", "")
        doc["critic_score"] = res.get("confidence_score", 0)
        return doc
        
    with ThreadPoolExecutor(max_workers=2) as executor:  # V2: Giảm từ 5→2 để tránh đốt daily quota Gemini
        evaluated_candidates = list(executor.map(_run_critic, top_candidates))
        
    for doc in evaluated_candidates:
        if doc.get("critic_approved"):
            final_approved.append(doc)
        else:
            with stats_lock:
                xray["rejection_reasons"]["low_relevance"] += 1
            
    logger.info(f"[MULTI-AGENT] Critic approved {len(final_approved)} / {len(top_candidates)} docs.")
    xray["adaptive"]["critic_yield"] = len(final_approved)
    hardened = final_approved

    # =========================================================================
    # EKRE V35.4: POST-FILTER SPIDER ARCHITECTURE
    # =========================================================================
    current_score = score_knowledge_base(hardened)
    MIN_DOCS_FOR_SPIDER = {"can_ban": 4, "tieu_chuan": 8, "chuyen_sau": 15}
    min_docs_required = MIN_DOCS_FOR_SPIDER.get(quy_mo, 8)
    unique_doc_count = len(set(d.get("title", "") for d in hardened))
    
    needs_spider_by_score = current_score < target_score
    needs_spider_by_docs = unique_doc_count < min_docs_required
    
    if needs_spider_by_score or needs_spider_by_docs:
        reason = []
        if needs_spider_by_score: reason.append(f"Score={current_score:.1f}<{target_score}")
        if needs_spider_by_docs: reason.append(f"Docs={unique_doc_count}<{min_docs_required}")
        logger.warning(f"[EKRE-V35.4] Post-Filter KB Under-spec ({', '.join(reason)}). Agent 4 (Spider) is activating...")
        
        spider_limit = 15 if quy_mo == "chuyen_sau" else 10
        selected_links = agent_link_curator(search_topic, all_internal_links, api_key_openai, max_links=spider_limit, truth_seed=truth_seed, search_model=search_model)
        
        spider_queries = []
        if selected_links:
            logger.info(f"[MULTI-AGENT] 🕸️ Agent 4 selected {len(selected_links)} internal links for deep spidering.")
            spider_queries = [{"title": link, "lang": primary_lang, "reason": "Spidering Expansion"} for link in selected_links]
        else:
            logger.warning(f"[MULTI-AGENT] 🕸️ Agent 4 could not find valuable links. Falling back to Gemini Expansion...")
            from dich_vu.gemini_da_buoc import generate_related_topics_gemini
            extra_topics = generate_related_topics_gemini(search_topic, all_raw_docs, quy_mo, api_keys_list)
            if extra_topics:
                extra_titles = multi_agent_identify_wiki_titles(f"{search_topic}: {', '.join(extra_topics)}", quy_mo, api_key_openai, is_expansion=True, search_model=search_model)
                spider_queries = []
                for t in extra_titles:
                    if isinstance(t, dict):
                        t_copy = dict(t)
                        t_copy["reason"] = "Gemini Expansion"
                        spider_queries.append(t_copy)
                    else:
                        spider_queries.append({"title": t, "lang": "vi", "reason": "Gemini Expansion"})

        if spider_queries:
            with ThreadPoolExecutor(max_workers=3) as executor:
                exp_results = list(executor.map(lambda x: fetch_title(x, sr_limit=2), spider_queries))
            
            new_raw = []
            for r in exp_results:
                if r: new_raw.extend(r)
                
            if new_raw:
                logger.info(f"[EKRE-V35.4] Spider fetched {len(new_raw)} docs. Filtering...")
                new_scored = hybrid_semantic_filter(new_raw, search_topic, search_topic, api_key_openai, threshold=CauHinh.EKRE_MIN_SIM_FLOOR)
                new_scored = sorted(new_scored, key=lambda x: x.get("relevance_score", 0), reverse=True)[:15]
                
                if new_scored:
                    logger.info(f"[MULTI-AGENT] Sending {len(new_scored)} spider candidates to Critic...")
                    with ThreadPoolExecutor(max_workers=2) as executor: # V2: Giảm từ 5→2 để tránh đốt daily quota
                        eval_new = list(executor.map(_run_critic, new_scored))
                    
                    spider_approved = 0
                    for doc in eval_new:
                        if doc.get("critic_approved"):
                            q = compute_quality_score(doc)
                            if q >= CauHinh.EKRE_MIN_QUALITY_FLOOR:
                                doc["is_low_priority"] = q < CauHinh.EKRE_QUALITY_STANDARD
                                doc["quality_score"] = q
                                hardened.append(doc)
                                all_raw_docs.append(doc)
                                spider_approved += 1
                    logger.info(f"[MULTI-AGENT] Critic approved {spider_approved} / {len(new_scored)} spider docs.")

    # --- Step 3: Diversity Coverage Check & Final Expansion ---
    unique_topics_count = len({d.get("subtopic") for d in hardened})
    dropped_count = len(all_raw_docs) - len(hardened)
    logger.info(
        f"[EKRE-V26.2] Post-Gate → Diversity:{unique_topics_count} clusters | "
        f"Yield:{len(hardened)} | QualityDropped:{dropped_count}"
    )

    if unique_topics_count < 5 and quy_mo == "chuyen_sau":
        logger.warning(f"[EKRE-V26.2] Critical Low Diversity ({unique_topics_count} < 5). Triggering final niche expansion...")
        extra_titles = multi_agent_identify_wiki_titles(
            f"{search_topic} (các khía cạnh chuyên sâu và cơ chế cốt lõi)", "can_ban", api_key_openai, is_expansion=True, search_model=search_model
        )
        niche_floor = CauHinh.EKRE_MIN_SIM_FLOOR  # Nới lỏng tối đa cho niche expansion
        with ThreadPoolExecutor(max_workers=3) as executor:
            for r in executor.map(fetch_title, extra_titles):
                if r:
                    new_scored = hybrid_semantic_filter(r, search_topic, search_topic, api_key_openai, threshold=niche_floor)
                    for nd in new_scored:
                        q = compute_quality_score(nd)
                        if q >= CauHinh.EKRE_MIN_QUALITY_FLOOR:
                            nd["is_low_priority"] = q < CauHinh.EKRE_QUALITY_STANDARD
                            nd["quality_score"] = q
                            hardened.append(nd)

    # --- Step 5: Final Deduplication & Cleanup ---
    hardened = deduplicate_by_embedding(hardened, api_key_openai, threshold=0.92, anchors=ai_titles)

    # --- Step 6: Final Stats Trace ---
    avg_len     = sum(len(d.get("text", "")) for d in hardened) / max(1, len(hardened))
    final_sims  = [d.get("relevance_score", 0) for d in hardened]
    avg_sim     = statistics.mean(final_sims) if final_sims else 0.0
    low_p_count = sum(1 for d in hardened if d.get("is_low_priority", False))

    logger.info(
        f"[STRUCTURE] Yield={len(hardened)} | AvgLen={avg_len:.0f} | AvgSim={avg_sim:.3f} | "
        f"Diversity={unique_topics_count} | LowPriority={low_p_count} | "
        f"Confidence={adaptive_analytics.get('confidence_score', 0):.3f} | "
        f"StopReason={adaptive_analytics.get('stop_reason', 'N/A')}"
    )

    xray["stats"]["filtered"] = len(hardened)
    xray["stats"]["final"]    = len(hardened)
    xray["stats"]["avg_sim"]  = round(avg_sim, 4)
    xray["stats"]["low_priority_count"] = low_p_count
    xray["stats"]["stop_reason"] = adaptive_analytics.get("stop_reason", "N/A")
    xray["stats"]["confidence_score"] = adaptive_analytics.get("confidence_score", 0.0)

    # V29.1: Build evaluated_docs list for UI
    evaluated_docs = []
    hardened_ids = {d.get("id") for d in hardened}
    is_embedding_failed = adaptive_analytics.get("stop_reason") == "EMBEDDING_API_FAILED"
    
    for d in all_raw_docs:
        status = "kept" if d.get("id") in hardened_ids else "dropped"
        # Identify drop reason mapping roughly
        if status == "kept":
            reason = "Đạt chuẩn (Multi-Agent)"
        elif d.get("critic_reason"):
            reason = f"Critic Loại: {d.get('critic_reason')} (Score: {d.get('critic_score', 0)})"
        elif is_embedding_failed:
            reason = "Lỗi API Google Quota (Không thể Vector hóa)"
        elif d.get("is_low_priority"):
            reason = "Điểm Vector thấp (Soft-kept)"
        else:
            reason = "Loại bỏ (Nhiễu/Trùng/Vector kém)"
            
        evaluated_docs.append({
            "title": d.get("title", ""),
            "url": d.get("url", ""),
            "status": status,
            "score": round(d.get("relevance_score", 0.0), 3),
            "reason": reason
        })
    
    # Sort docs: kept first, then high score
    evaluated_docs.sort(key=lambda x: (x["status"] == "kept", x["score"]), reverse=True)
    xray["evaluated_docs"] = evaluated_docs

    clean_docs = [lam_sach_trang(d) for d in hardened]
    return {
        "passages": chia_doan(clean_docs),
        "candidates": {d["title"]: {"url": d["url"], "lang": d["lang"]} for d in hardened},
        "hardened_docs": hardened,
        "xray": xray
    }

# --- LEGACY / UTILITY ---
def smart_search_crawl(missing_topics: list, ti_le_en: float = 0.8):
    if not missing_topics: return []
    from .lam_sach_van_ban import chia_doan, lam_sach_trang
    results = []
    def crawl_one(t):
        # Ưu tiên ngôn ngữ dựa trên tỉ lệ yêu cầu (V18.3)
        langs = ["en", "vi"] if random.random() < ti_le_en else ["vi", "en"]
        for lang in langs:
            titles = tim_kiem_tieu_de(lang, t, gioi_han=1)
            for title in titles:
                content, _, url = lay_noi_dung_va_lien_ket(lang, title)
                if content and len(content) > 500:
                    if lang == "en" and CauHinh.OPENAI_API_KEY:
                        logger.info(f"[CROSS-LINGUAL] Translating smart crawl English doc '{title}' to Vietnamese...")
                        content = dich_tai_lieu_en_sang_vi(content, CauHinh.OPENAI_API_KEY)
                        title = f"{title} (Bản dịch)"
                        lang = "vi"
                    return {"title": title, "text": content, "url": url, "lang": lang, "id": str(uuid.uuid4())[:8]}
        return None
    with ThreadPoolExecutor(max_workers=3) as executor:
        found = [r for r in executor.map(crawl_one, missing_topics[:8]) if r]
    return chia_doan([lam_sach_trang(f) for f in found])

def tao_tai_lieu_tu_wikipedia(chu_de, so_trang_hat_giong=10, so_trang_lien_ket=0, quy_mo="tieu_chuan", **kwargs):
    """Legacy wrapper for backward compatibility."""
    from .vector_search import tao_vector_db
    res = ekre_discovery_engine(chu_de, CauHinh.GEMINI_API_KEYS, quy_mo, CauHinh.OPENAI_API_KEY)
    return res["passages"] # Simplified return for legacy paths
