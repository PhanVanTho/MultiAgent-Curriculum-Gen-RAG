# -*- coding: utf-8 -*-
"""
cli.py — Command-Line Interface cho hệ thống Tự động hóa Giáo trình (V32)
=========================================================================
Cho phép tạo giáo trình từ dòng lệnh mà không cần khởi động web server.

Sử dụng:
    python cli.py --chu_de "Trí tuệ nhân tạo" --dau_ra ./output
    python cli.py --chu_de "Blockchain" --quy_mo chuyen_sau --dau_ra ./output
    python cli.py --chu_de "Vật lý lượng tử" --ngon_ngu en --dau_ra ./output/physics
"""
import os
import sys
import json
import re
import uuid
import time
import copy
import argparse
import logging
import threading

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# --- Đảm bảo project root trong sys.path ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from cau_hinh import CauHinh

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("cli.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("CLI")

# --- SEMAPHORES (giống ung_dung.py) ---
OPENAI_SEMAPHORE = threading.BoundedSemaphore(6)
PASSAGES_LOCK = threading.RLock()
MAX_TOTAL_PASSAGES = 2000


# =========================================================================
# PIPELINE CONTEXT (tái sử dụng cấu trúc từ ung_dung.py)
# =========================================================================
class PipelineContext:
    def __init__(self, ma_cv, tieu_de, quy_mo, api_keys_list, passages_db,
                 global_map, terms, passages, candidates, openai_semaphore,
                 safety_class="SAFE", ngon_ngu="vi"):
        self.ma_cv = ma_cv
        self.tieu_de = tieu_de
        self.quy_mo = quy_mo
        self.api_keys_list = api_keys_list
        self._passages_db = passages_db
        self.global_map = global_map
        self.terms = terms
        self.passages = passages
        self.candidates = candidates
        self.openai_semaphore = openai_semaphore
        self.safety_class = safety_class
        self.ngon_ngu = ngon_ngu
        self.start_time = time.time()

    @property
    def passages_db(self):
        with PASSAGES_LOCK:
            return list(self._passages_db)

    @passages_db.setter
    def passages_db(self, value):
        with PASSAGES_LOCK:
            self._passages_db = value

    def get_logger_prefix(self):
        return f"CLI {self.ma_cv[:8]} | {self.quy_mo.upper()}"


# =========================================================================
# PROGRESS TRACKER (thay thế CONG_VIEC dict cho CLI)
# =========================================================================
class CLIProgress:
    """Hiển thị tiến trình trên console thay vì lưu vào dict."""
    def __init__(self, tieu_de):
        self.tieu_de = tieu_de
        self.start_time = time.time()

    def update(self, pct, msg):
        elapsed = time.time() - self.start_time
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\r  [{bar}] {pct:3d}% | {msg} (T+{elapsed:.0f}s)", end="", flush=True)
        if pct >= 100:
            print()  # Xuống dòng khi hoàn tất

    def log(self, msg):
        elapsed = time.time() - self.start_time
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] {msg} (T+{elapsed:.1f}s)")


# =========================================================================
# MAIN PIPELINE (tái sử dụng logic từ ung_dung.py, không cần Flask)
# =========================================================================
def run_cli_pipeline(chu_de: str, quy_mo: str, ngon_ngu: str, dau_ra: str):
    """
    Chạy toàn bộ pipeline tạo giáo trình từ command line.
    Trả về đường dẫn thư mục chứa kết quả.
    """
    from dich_vu.lay_wikipedia import ekre_discovery_engine, score_knowledge_base
    from dich_vu.vector_search import tao_vector_db, tim_kiem_vector, tim_kiem_vector_with_llm_rerank
    from dich_vu.xuat_tai_lieu.xuat_docx import xuat_docx
    from dich_vu.xuat_tai_lieu.xuat_pdf import xuat_pdf
    from dich_vu.kiem_tra_cau_truc_json import clean_title_numbering

    ma_cv = str(uuid.uuid4())
    progress = CLIProgress(chu_de)

    print(f"\n{'='*60}")
    print(f"  📚 HỆ THỐNG TẠO GIÁO TRÌNH TỰ ĐỘNG (CLI Mode)")
    print(f"{'='*60}")
    print(f"  Chủ đề  : {chu_de}")
    print(f"  Quy mô  : {quy_mo}")
    print(f"  Ngôn ngữ: {ngon_ngu}")
    print(f"  Đầu ra  : {os.path.abspath(dau_ra)}")
    print(f"  Job ID  : {ma_cv[:8]}")
    print(f"{'='*60}\n")

    start_time = time.time()

    # ── Step 0: Safety Classification ──
    progress.update(5, "Kiểm tra an toàn chủ đề...")
    from dich_vu.safety_router import classify_topic, reframe_topic, generate_safe_title, get_block_message
    safety_res = classify_topic(chu_de, CauHinh.OPENAI_API_KEY)
    safety_class = safety_res.get("classification", "SAFE")

    if safety_class in ["BLOCK", "BLOCK_LANG"]:
        block_msg = get_block_message(safety_res)
        error_text = block_msg["message"] if block_msg else safety_res.get("reason")
        if block_msg and block_msg.get("suggestion"):
            error_text += f"\n\n{block_msg['suggestion']}"
        print(f"\n  ❌ CHỦ ĐỀ BỊ CHẶN:\n{error_text}")
        sys.exit(1)

    ekre_query = chu_de
    if safety_class == "REFRAME":
        ekre_query = reframe_topic(chu_de)
        chu_de = generate_safe_title(chu_de)
        progress.log(f"⚠️  Chủ đề nhạy cảm. Chuyển sang phân tích học thuật: {ekre_query}")

    # ── Step 1: EKRE Discovery ──
    progress.update(10, "EKRE Discovery — Thu thập tri thức...")
    ekre_res = ekre_discovery_engine(
        ekre_query,
        api_keys_list=CauHinh.GEMINI_API_KEYS,
        quy_mo=quy_mo,
        api_key_openai=CauHinh.OPENAI_API_KEY
    )
    passages = ekre_res.get("passages", [])
    candidates = ekre_res.get("candidates", {})
    hardened_docs = ekre_res.get("hardened_docs", [])
    xray = ekre_res.get("xray", {})

    progress.log(f"Discovery hoàn tất: {len(candidates)} nguồn, {len(passages)} passages")

    # ── Reliability Gate ──
    reliable_docs = [
        d for d in hardened_docs
        if d.get("quality_score", 0) >= CauHinh.EKRE_MIN_QUALITY_FLOOR
        and not d.get("is_low_priority", False)
    ]
    confidence = xray.get("stats", {}).get("confidence_score", 0)

    if len(reliable_docs) == 0 or confidence < 0.25:
        print(f"\n  ❌ Thông tin tìm kiếm của bạn trên Wikipedia không đủ để viết một bài giáo trình.")
        sys.exit(1)

    # ── Data Sufficiency Gate ──
    kb_score = score_knowledge_base(hardened_docs)
    SUFFICIENCY_THRESHOLDS = {"can_ban": 15, "tieu_chuan": 30, "chuyen_sau": 60}
    min_threshold = SUFFICIENCY_THRESHOLDS.get(quy_mo, 30)

    # --- TOPIC PRESENCE CHECK (V31.8 — Diacritics-aware) ---
    from dich_vu.lam_sach_van_ban import remove_diacritics
    VIET_STOPWORDS = {
        "tổng", "quan", "về", "giới", "thiệu", "cơ", "bản", "nâng", "cao",
        "chuyên", "sâu", "nhập", "môn", "đại", "cương", "khái", "niệm",
        "của", "và", "các", "trong", "cho", "với", "từ", "đến", "là",
        "một", "những", "được", "có", "này", "theo", "tại", "trên",
        "tong", "ve", "gioi", "co", "ban", "nang",
        "chuyen", "nhap", "dai", "cuong", "khai",
        "cua", "va", "cac", "trong", "voi", "tu", "den", "la",
        "mot", "nhung", "duoc", "nay", "tai"
    }
    topic_lower = chu_de.lower().strip()
    core_words = [w for w in topic_lower.split() if w not in VIET_STOPWORDS and len(w) > 1]
    core_phrase = " ".join(core_words)
    core_phrase_nodiac = remove_diacritics(core_phrase).lower()
    
    subphrases = []
    if len(core_words) >= 2:
        for length in range(len(core_words), 1, -1):
            for start in range(len(core_words) - length + 1):
                sp = " ".join(core_words[start:start+length])
                subphrases.append(sp)
    elif core_phrase:
        subphrases = [core_phrase]
        
    subphrases_nodiac = [remove_diacritics(sp).lower() for sp in subphrases]
    
    docs_mentioning_topic = 0
    for d in hardened_docs:
        doc_text = (d.get("text", "") + " " + d.get("title", "")).lower()
        doc_text_nodiac = remove_diacritics(doc_text)
        matched = any(
            sp in doc_text or sp_nd in doc_text_nodiac
            for sp, sp_nd in zip(subphrases, subphrases_nodiac)
        )
        if matched:
            docs_mentioning_topic += 1
            
    topic_presence_ratio = docs_mentioning_topic / max(len(hardened_docs), 1)
    avg_sim = xray.get("stats", {}).get("avg_sim", 1.0)
    
    is_topic_absent = (docs_mentioning_topic == 0) or (topic_presence_ratio < 0.10 and avg_sim < 0.35)
    if is_topic_absent and avg_sim < 0.45:
        kb_score = 0

    if kb_score < min_threshold:
        if is_topic_absent or topic_presence_ratio < 0.10:
            print(f"\n  ❌ Thông tin tìm kiếm của bạn trên Wikipedia không đủ để viết một bài giáo trình.")
            sys.exit(1)
            
        print(f"\n  ⚠️  DỮ LIỆU CHƯA ĐỦ cho quy mô '{quy_mo}' (Score: {kb_score:.1f} < {min_threshold})")
        SCALE_DOWNGRADE = {"chuyen_sau": "tieu_chuan", "tieu_chuan": "can_ban"}
        if quy_mo in SCALE_DOWNGRADE:
            lower = SCALE_DOWNGRADE[quy_mo]
            if kb_score >= SUFFICIENCY_THRESHOLDS[lower]:
                print(f"     → Tự động hạ quy mô xuống '{lower}'")
                quy_mo = lower
            else:
                print(f"\n  ❌ Thông tin tìm kiếm của bạn trên Wikipedia không đủ để viết một bài giáo trình.")
                sys.exit(1)
        else:
            print(f"\n  ❌ Thông tin tìm kiếm của bạn trên Wikipedia không đủ để viết một bài giáo trình.")
            sys.exit(1)

    # ── Create Vector DB ──
    progress.update(20, "Xây dựng Vector Database...")
    passages_db = tao_vector_db(passages, api_key=CauHinh.OPENAI_API_KEY)
    global_map = {p['id']: p for p in passages_db}

    # ── Initialize Context ──
    ctx = PipelineContext(
        ma_cv=ma_cv, tieu_de=chu_de, quy_mo=quy_mo,
        api_keys_list=CauHinh.GEMINI_API_KEYS,
        passages_db=passages_db, global_map=global_map,
        terms=[], passages=passages, candidates=candidates,
        openai_semaphore=OPENAI_SEMAPHORE,
        safety_class=safety_class, ngon_ngu=ngon_ngu
    )

    # ── Step 2: Term Extraction & Outline ──
    progress.update(30, "Trích xuất thuật ngữ & xây dựng dàn ý...")
    from dich_vu.openai_da_buoc import (
        xay_dung_metadata_toan_dien, trich_xuat_thuat_ngu,
        nhom_thuat_ngu_va_tao_dan_y, tao_dan_y_tu_passages,
        xac_dinh_ngan_sach_thuat_ngu, get_structure_config
    )

    num_articles = len(candidates) if candidates else 1
    budget = xac_dinh_ngan_sach_thuat_ngu(num_articles, 0, quy_mo=quy_mo)
    progress.log(f"Term budget: {budget['core_count']} core, {budget['support_count']} supporting")

    # Term Extraction
    metadata_list = xay_dung_metadata_toan_dien(passages)
    terms_data = trich_xuat_thuat_ngu(
        passages, api_key=CauHinh.OPENAI_API_KEY,
        target_core=budget["core_count"],
        target_support=budget["support_count"],
        semaphore=OPENAI_SEMAPHORE
    )
    ctx.terms = terms_data.get("core_terms", []) + terms_data.get("supporting_terms", [])
    progress.log(f"Trích xuất xong {len(ctx.terms)} thuật ngữ")

    # Outline Generation
    progress.update(40, "Sinh dàn ý học thuật...")
    try:
        outline_data = nhom_thuat_ngu_va_tao_dan_y(
            terms_data, api_key=CauHinh.OPENAI_API_KEY,
            chu_de=chu_de, so_chuong=0, quy_mo=quy_mo,
            semaphore=OPENAI_SEMAPHORE, ngon_ngu=ngon_ngu
        )
        if not outline_data or not outline_data.get("outline"):
            raise ValueError("Outline empty")
    except Exception as e:
        progress.log(f"⚠️  Tier 1 Outline failed ({e}). Trying Tier 2...")
        outline_data = tao_dan_y_tu_passages(
            chu_de, passages, api_key=CauHinh.OPENAI_API_KEY,
            quy_mo=quy_mo, semaphore=OPENAI_SEMAPHORE
        )

    raw_outline = outline_data.get("outline", [])
    total_sections = sum(len(c.get("sections", [])) for c in raw_outline)
    progress.log(f"Dàn ý: {len(raw_outline)} chương, {total_sections} mục")

    # ── Step 2.5: Outline-Driven Iterative Retrieval (Gap-Filling) ──
    progress.update(45, "Kiểm toán lỗ hổng tri thức (Knowledge Gap-Filling)...")
    from dich_vu.gap_filler import identify_knowledge_gaps, fill_knowledge_gaps
    
    gaps = identify_knowledge_gaps(raw_outline, ctx.passages_db, CauHinh.OPENAI_API_KEY, chu_de)
    if gaps:
        progress.log(f"Phát hiện {len(gaps)} lỗ hổng tri thức. Đang kích hoạt tìm kiếm bù đắp...")
        new_passages = fill_knowledge_gaps(gaps, CauHinh.GEMINI_API_KEYS, CauHinh.OPENAI_API_KEY, chu_de)
        if new_passages:
            # Gộp passages mới vào DB
            progress.log(f"Đang lập chỉ mục (Vectorizing) {len(new_passages)} đoạn văn bổ sung...")
            from dich_vu.vector_search import tao_vector_db
            new_passages_db = tao_vector_db(new_passages, api_key=CauHinh.OPENAI_API_KEY)
            
            # Cập nhật DB hiện tại
            ctx.passages.extend(new_passages)
            # Do ctx.passages_db là list, nếu gán bằng getter/setter property cần chú ý (đã có setter trong PipelineContext)
            updated_db = ctx.passages_db
            updated_db.extend(new_passages_db)
            ctx.passages_db = updated_db
            
            # Cập nhật global map
            for p in new_passages_db:
                ctx.global_map[str(p['id'])] = p
                
            progress.log(f"Đã cập nhật Vector DB. Tổng cộng: {len(ctx.passages_db)} passages.")
        else:
            progress.log("Không tìm thấy dữ liệu bù đắp hữu ích.")
    else:
        progress.log("Cơ sở dữ liệu đủ độ phủ, không có lỗ hổng.")

    # ── Step 3: Content Generation ──
    progress.update(50, "Biên soạn nội dung (Parallel Writing)...")

    # Import parallel_generate dependencies
    from dich_vu.openai_da_buoc import viet_noi_dung_batch_sections, viet_rut_gon_rescue
    from dich_vu.kiem_tra_cau_truc_json import safe_section_fix, safe_parse_json
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def process_chapter_cli(ctx, chap, outline_data):
        """Xử lý 1 chương — tương tự process_chapter trong ung_dung.py."""
        chap_title = chap.get("title", "Không tên")
        sections = chap.get("sections", [])
        mode = outline_data.get("mode", "standard")
        
        result_sections = []
        dynamic_top_k = {"can_ban": 7, "tieu_chuan": 12, "chuyen_sau": 18}.get(ctx.quy_mo, 12)
        
        # Batch processing (giống process_batch_sections_task)
        relevant_passages_list = []
        for s_info in sections:
            s_title = s_info.get("title", "Mục mới")
            hits = tim_kiem_vector_with_llm_rerank(
                query=f"{chap_title} {s_title}",
                passages_db=ctx.passages_db,
                api_key=CauHinh.OPENAI_API_KEY,
                top_k=dynamic_top_k,
                candidate_n=min(30, len(ctx.passages_db)),
                chapter_title=chap_title,
                section_title=s_title
            )
            relevant_passages_list.append(hits)
        
        try:
            res = viet_noi_dung_batch_sections(
                chu_de=ctx.tieu_de, chapter_title=chap_title,
                sections_info=sections, relevant_passages_list=relevant_passages_list,
                api_key=CauHinh.OPENAI_API_KEY, mode=mode,
                semaphore=ctx.openai_semaphore, ngon_ngu=ctx.ngon_ngu,
                quy_mo=ctx.quy_mo
            )
            if res.get("status") == "success":
                raw_json = res.get("raw_text", "{}")
                parsed = json.loads(raw_json)
                result_sections = parsed.get("sections", [])
        except Exception as e:
            logger.error(f"Batch write failed for '{chap_title}': {e}")
        
        # Fallback: rescue rút gọn cho sections thiếu
        if len(result_sections) < len(sections):
            for i in range(len(result_sections), len(sections)):
                s_title = sections[i].get("title", "Mục")
                try:
                    res_rescue = viet_rut_gon_rescue(
                        ctx.tieu_de, s_title,
                        relevant_passages_list[i] if i < len(relevant_passages_list) else [],
                        api_key=CauHinh.OPENAI_API_KEY,
                        semaphore=ctx.openai_semaphore
                    )
                    if res_rescue.get("status") == "success":
                        raw_json = res_rescue.get("raw_text", "{}")
                        parsed = json.loads(raw_json)
                        content = parsed.get("content", "Nội dung đang cập nhật.")
                        result_sections.append({"title": s_title, "content": content})
                    else:
                        result_sections.append({"title": s_title, "content": "Nội dung đang cập nhật."})
                except Exception:
                    result_sections.append({"title": s_title, "content": "Nội dung đang cập nhật."})
        
        return {"title": chap_title, "sections": result_sections}

    # Parallel chapter processing
    final_chapters = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(process_chapter_cli, ctx, chap, outline_data): i
            for i, chap in enumerate(raw_outline)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                result = future.result()
                final_chapters.append((idx, result))
                done = len(final_chapters)
                pct = 50 + int(35 * done / len(raw_outline))
                progress.update(pct, f"Biên soạn {done}/{len(raw_outline)} chương...")
            except Exception as e:
                logger.error(f"Chapter {idx} failed: {e}")
                final_chapters.append((idx, {"title": raw_outline[idx].get("title", ""), "sections": []}))
    
    # Sắp xếp lại theo thứ tự gốc
    final_chapters.sort(key=lambda x: x[0])
    final_chapters = [ch for _, ch in final_chapters]
    progress.log(f"Biên soạn xong {len(final_chapters)} chương")

    # ── Step 4: Citation Processing ──
    progress.update(88, "Hậu xử lý trích dẫn...")
    all_original_passages = {str(p['id']): p for p in ctx.passages_db}
    url_to_new_id = {}
    ordered_refs = []

    for chap in final_chapters:
        for sec in chap.get("sections", []):
            found_ids = re.findall(r'\[(\w+)\]', sec.get("content", ""))
            for oid in found_ids:
                if oid in all_original_passages:
                    p = all_original_passages[oid]
                    url = p.get('url', '')
                    if url and url not in url_to_new_id:
                        new_id = len(url_to_new_id) + 1
                        url_to_new_id[url] = new_id
                        ordered_refs.append({"id": new_id, "url": url, "title": p.get('title', 'Nguồn')})

    for chap in final_chapters:
        for sec in chap.get("sections", []):
            content = sec.get("content", "")
            found_ids = re.findall(r'\[(\w+)\]', content)
            sec_citations = []
            added_urls = set()

            for oid in set(found_ids):
                if oid in all_original_passages:
                    url = all_original_passages[oid].get('url', '')
                    if url in url_to_new_id:
                        nid = url_to_new_id[url]
                        # CLI: Dùng text citation thay vì HTML
                        content = content.replace(f"[{oid}]", f"[{nid}]")
                        if url not in added_urls:
                            node = next(r for r in ordered_refs if r["url"] == url)
                            sec_citations.append(node)
                            added_urls.add(url)
                else:
                    content = re.sub(rf"\[{oid}\]", "", content)

            sec["content"] = content
            sec["citations"] = sec_citations

    # ── Step 5: Package & Export ──
    progress.update(92, "Đóng gói giáo trình...")

    book_export = {"title": chu_de, "chapters": []}
    for chap in final_chapters:
        c_title = clean_title_numbering(chap.get("title", "Không tên"))
        new_chap = {"title": c_title, "sections": []}
        for sec in chap.get("sections", []):
            s_title = clean_title_numbering(sec.get("title", "Mục"))
            new_chap["sections"].append({
                "title": s_title,
                "content": sec.get("content", ""),
                "citations": sec.get("citations", [])
            })
        book_export["chapters"].append(new_chap)

    all_refs = ordered_refs
    
    # Lấy danh sách đoạn văn (content) gốc từ passages_db
    original_contexts = [p.get("content", "") for p in passages_db] if passages_db else []
    
    ket_qua = {
        "topic": chu_de, 
        "book_vi": book_export, 
        "references": all_refs,
        "contexts": original_contexts  # Lưu vào JSON để RAGAS sử dụng
    }

    # Phiên bản sạch (không trích dẫn)
    def strip_citations(text):
        if not text:
            return ""
        clean = re.sub(r'\[\d+\]', '', text)
        return clean

    book_plain = copy.deepcopy(book_export)
    for chap in book_plain.get("chapters", []):
        for sec in chap.get("sections", []):
            sec["content"] = strip_citations(sec.get("content", ""))
            sec["citations"] = []
    ket_qua_plain = {"topic": chu_de, "book_vi": book_plain, "references": []}

    # ── Tạo thư mục đầu ra & Xuất file ──
    os.makedirs(dau_ra, exist_ok=True)
    safe_name = re.sub(r'[\\/*?:"<>|]', '', chu_de).strip()

    p_json = os.path.join(dau_ra, f"{safe_name}.json")
    p_docx = os.path.join(dau_ra, f"{safe_name}.docx")
    p_pdf = os.path.join(dau_ra, f"{safe_name}.pdf")
    p_docx_plain = os.path.join(dau_ra, f"{safe_name} (bản sạch).docx")
    p_pdf_plain = os.path.join(dau_ra, f"{safe_name} (bản sạch).pdf")

    progress.update(95, "Xuất JSON...")
    with open(p_json, "w", encoding="utf-8") as f:
        json.dump(ket_qua, f, ensure_ascii=False, indent=2)

    progress.update(96, "Xuất DOCX...")
    xuat_docx(ket_qua, p_docx)
    xuat_docx(ket_qua_plain, p_docx_plain)

    progress.update(98, "Xuất PDF...")
    xuat_pdf(ket_qua, p_pdf)
    xuat_pdf(ket_qua_plain, p_pdf_plain)

    progress.update(100, "HOÀN TẤT!")

    # ── Summary ──
    elapsed = time.time() - start_time
    tong_ky_tu = sum(
        len(sec.get("content", ""))
        for chap in book_export.get("chapters", [])
        for sec in chap.get("sections", [])
    )

    print(f"\n{'='*60}")
    print(f"  ✅ GIÁO TRÌNH ĐÃ TẠO THÀNH CÔNG!")
    print(f"{'='*60}")
    print(f"  📁 Thư mục : {os.path.abspath(dau_ra)}")
    print(f"  📄 Files   :")
    print(f"     • {safe_name}.pdf")
    print(f"     • {safe_name}.docx")
    print(f"     • {safe_name} (bản sạch).pdf")
    print(f"     • {safe_name} (bản sạch).docx")
    print(f"     • {safe_name}.json")
    print(f"  📊 Thống kê:")
    print(f"     • {len(final_chapters)} chương, {total_sections} mục")
    print(f"     • {tong_ky_tu:,} ký tự")
    print(f"     • {len(all_refs)} nguồn tham khảo")
    print(f"  ⏱️  Thời gian: {elapsed:.0f}s ({elapsed/60:.1f} phút)")
    print(f"{'='*60}\n")

    return dau_ra


# =========================================================================
# ARGUMENT PARSER
# =========================================================================
def main():
    parser = argparse.ArgumentParser(
        description="🎓 Hệ thống Tự động hóa Giáo trình — CLI Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python cli.py --chu_de "Trí tuệ nhân tạo" --dau_ra ./output
  python cli.py --chu_de "Blockchain" --quy_mo chuyen_sau --dau_ra ./output/blockchain
  python cli.py --chu_de "Quantum Computing" --ngon_ngu en --dau_ra ./output/quantum
        """
    )
    parser.add_argument(
        "--chu_de", required=True,
        help="Chủ đề giáo trình (VD: 'Trí tuệ nhân tạo')"
    )
    parser.add_argument(
        "--dau_ra", required=True,
        help="Thư mục đầu ra chứa file PDF, DOCX, JSON"
    )
    parser.add_argument(
        "--quy_mo", default="tieu_chuan",
        choices=["can_ban", "tieu_chuan", "chuyen_sau"],
        help="Quy mô giáo trình (mặc định: tieu_chuan)"
    )
    parser.add_argument(
        "--ngon_ngu", default="vi",
        choices=["vi", "en"],
        help="Ngôn ngữ đầu ra (mặc định: vi)"
    )
    parser.add_argument(
        "--openai_key", default=None,
        help="Khóa OpenAI API Key tùy chọn (đè cấu hình hệ thống)"
    )
    parser.add_argument(
        "--gemini_keys", default=None,
        help="Danh sách khóa Gemini API Key tùy chọn, phân tách bằng dấu phẩy (đè cấu hình hệ thống)"
    )

    args = parser.parse_args()

    # Override config keys if provided
    if args.openai_key:
        CauHinh.OPENAI_API_KEY = args.openai_key.strip()
    if args.gemini_keys:
        keys_list = [k.strip() for k in args.gemini_keys.split(",") if k.strip()]
        if keys_list:
            CauHinh.GEMINI_API_KEYS = keys_list

    # Validate
    if len(args.chu_de.strip()) < 2:
        print("❌ Chủ đề phải có ít nhất 2 ký tự.")
        sys.exit(1)

    run_cli_pipeline(
        chu_de=args.chu_de.strip(),
        quy_mo=args.quy_mo,
        ngon_ngu=args.ngon_ngu,
        dau_ra=args.dau_ra
    )


if __name__ == "__main__":
    main()
