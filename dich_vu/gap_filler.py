# -*- coding: utf-8 -*-
"""
Gap Filler Module (Outline-Driven Iterative Retrieval)
Tự động phát hiện các lỗ hổng tri thức (Knowledge Gaps) trong dàn ý so với Vector DB hiện tại,
và kích hoạt tìm kiếm mở rộng trên Wikipedia để bù đắp trước khi viết.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dich_vu.vector_search import tim_kiem_vector
from dich_vu.lay_wikipedia import ekre_discovery_engine, dem_so_tu_word
from cau_hinh import CauHinh

logger = logging.getLogger(__name__)

# Ngưỡng 0.54 là ngưỡng tối ưu cho gemini-embedding-2.
# Sử dụng cơ chế max(top_scores) thay vì trung bình để tránh loãng điểm.
GAP_THRESHOLD_SIMILARITY = 0.54  # Điểm tương đồng tối thiểu để coi là có đủ dữ liệu

def identify_knowledge_gaps(outline: list, passages_db: list, api_key: str, topic: str, custom_section_words: int = None, check_cancel=None) -> list:
    """
    Quét qua toàn bộ dàn ý để tìm những mục có điểm tương đồng với kho tài liệu < GAP_THRESHOLD
    HOẶC không đủ dung lượng tri thức để đáp ứng yêu cầu số từ của mục đó.
    """
    gaps = []
    logger.info(f"🔍 [Gap Filler] Bắt đầu kiểm toán {len(outline)} chương so với cơ sở dữ liệu ({len(passages_db)} passages).")
    
    # Xác định số từ mục tiêu cho mỗi mục cấp 2
    target_words = int(custom_section_words) if custom_section_words else 400
    min_ref_words = target_words
    
    for chap in outline:
        chap_title = chap.get("title", "")
        for sec in chap.get("sections", []):
            if check_cancel: check_cancel()
            sec_title = sec.get("title", "")
            sec_title_lower = sec_title.lower()
            if any(kw in sec_title_lower for kw in ["bài tập", "ôn tập", "thực hành", "tóm tắt", "exercise", "review", "practice"]):
                continue
            query = f"{topic} {chap_title} {sec_title}"
            
            # Query top_k=6 để quét được nhiều đoạn tham chiếu hơn nhằm tính tổng lượng tri thức
            hits = tim_kiem_vector(query, passages_db, api_key, top_k=6)
            
            # TỐI ƯU HÓA: Dùng MAX score thay vì AVG score cho sự tương đồng.
            if hits:
                top_scores = [hit.get("score", 0) for hit in hits[:3]]
                best_score = max(top_scores)
                # Tính tổng số từ của các đoạn văn bản có độ liên quan tốt (score >= 0.50)
                relevant_hits = [hit for hit in hits if hit.get("score", 0) >= 0.50]
                total_words = sum(dem_so_tu_word(hit.get("content", "")) for hit in relevant_hits)
            else:
                best_score = 0.0
                total_words = 0
                
            is_gap = False
            reason = ""
            
            # Kiểm tra 1: Độ tương đồng chất lượng
            if best_score < GAP_THRESHOLD_SIMILARITY:
                is_gap = True
                reason = f"Độ tương đồng thấp ({best_score:.3f} < {GAP_THRESHOLD_SIMILARITY})"
            # Kiểm tra 2: Đủ dung lượng tri thức
            elif total_words < min_ref_words:
                is_gap = True
                reason = f"Thiếu dung lượng tri thức ({total_words} từ < {min_ref_words} từ cần thiết)"
                
            if is_gap:
                logger.warning(f"  ⚠️ LỖ HỔNG TRI THỨC: '{sec_title}' ({reason})")
                gaps.append({
                    "chapter": chap_title,
                    "section": sec_title,
                    "query": query,
                    "score": best_score,
                    "reason": reason
                })
            else:
                logger.debug(f"  ✅ Đủ dữ liệu: '{sec_title}' (Best Score: {best_score:.3f}, Words: {total_words} >= {min_ref_words})")
                
    return gaps

def fill_knowledge_gaps(gaps: list, api_keys_list: list, api_key_openai: str, base_topic: str, is_custom_flow: bool = False, custom_section_words: int = None, check_cancel=None) -> list:
    """
    Kích hoạt tìm kiếm bù đắp cho các lỗ hổng.
    Sử dụng chính ekre_discovery_engine (cơ chế spidering tự động của hệ thống).
    """
    if not gaps:
        return []
        
    logger.info(f"🚀 [Gap Filler] Bắt đầu tìm kiếm bù đắp cho {len(gaps)} lỗ hổng...")
    
    search_targets = []
    if is_custom_flow:
        # Custom Outline: Tìm kiếm trực tiếp từng mục nhỏ bị thiếu (không gộp, không bỏ sót)
        seen_queries = set()
        for g in gaps:
            sec_title = g["section"]
            query = f"{base_topic} {sec_title}"
            if query not in seen_queries:
                seen_queries.add(query)
                search_targets.append(query)
    else:
        # Auto Outline: Gom nhóm theo chương để tránh gọi API quá nhiều lần cho cùng 1 chủ đề
        grouped_queries = {}
        for g in gaps:
            chap = g["chapter"]
            if chap not in grouped_queries:
                grouped_queries[chap] = []
            grouped_queries[chap].append(g["section"])
            
        for chap, secs in grouped_queries.items():
            # Tạo query bao quát cho cả chương dựa trên các mục thiếu
            if len(secs) > 1:
                query = f"{base_topic} {chap} ({', '.join(secs[:2])})"
            else:
                query = f"{base_topic} {secs[0]}"
            search_targets.append(query)
        
    all_new_passages = []
    
    def search_worker(query):
        if check_cancel: check_cancel()
        logger.info(f"  -> Đang cào bù đắp: '{query}'")
        try:
            # Thêm timeout an toàn cho việc cào bù đắp (tránh treo toàn bộ job)
            # Truyền chapter_hints=[query] để bypass AI Brainstorming, tìm kiếm trực tiếp trên Wikipedia!
            res = ekre_discovery_engine(
                topic=query,
                api_keys_list=api_keys_list,
                quy_mo="can_ban", # Chỉ cào nhanh (3-5 bài) cho mục bù đắp
                api_key_openai=api_key_openai,
                original_topic=base_topic,
                search_model="gpt-4o-mini",
                chapter_hints=[query],
                custom_section_words=custom_section_words,
                check_cancel=check_cancel
            )
            return res.get("passages", [])
        except Exception as e:
            logger.error(f"  ❌ Lỗi Timeout/API khi cào bù đắp '{query}': {e}")
            return []
        
    # Chạy song song để tiết kiệm thời gian, với timeout cho futures
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(search_worker, q): q for q in search_targets}
        try:
            for future in as_completed(futures, timeout=150): # Timeout tối đa 2.5 phút cho bước bù đắp
                if check_cancel: check_cancel()
                q = futures[future]
                try:
                    passages = future.result()
                    if passages:
                        logger.info(f"  ✅ '{q}': Thu được {len(passages)} passages mới.")
                        all_new_passages.extend(passages)
                except Exception as e:
                    logger.error(f"  ❌ Lỗi/Timeout luồng cào '{q}': {e}")
        except Exception as timeout_ex:
            logger.warning(f"  ⚠️ Quá thời gian quy định cho Gap Filler ({timeout_ex}). Tạm dừng chờ cào bù đắp sớm.")
                
    logger.info(f"🎉 [Gap Filler] Hoàn tất bù đắp. Bổ sung tổng cộng {len(all_new_passages)} passages mới.")
    return all_new_passages
