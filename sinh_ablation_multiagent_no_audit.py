"""
ABLATION VARIANT 2: Multi-agent RAG WITHOUT Self-Evaluation  
=============================================================
TÁI SỬ DỤNG passages từ Proposed JSON (cùng knowledge base)
Full multi-agent flow nhưng BỎ ScholarlyAudit

Chỉ dùng OpenAI — tránh Gemini quota exhausted
"""
import os, sys, json, time, re, glob
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import threading

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SEMAPHORE = threading.Semaphore(3)
OUTPUT_DIR = r"d:\tu_dong_giao_trinh\ThucNghiem_KetQua\Ablation_MultiAgent_NoAudit"
os.makedirs(OUTPUT_DIR, exist_ok=True)

JSON_DIR = r"d:\tu_dong_giao_trinh\du_lieu\dau_ra\json"
TOPICS = [
    "Trí tuệ nhân tạo", "Biến đổi khí hậu", "Tin sinh học",
    "Tâm lý học nhận thức", "An ninh mạng", "Công nghệ chuỗi khối",
    "Xã hội học", "Công nghệ nano", "Kỹ thuật phần mềm", "Điện toán lượng tử"
]

def find_best_json(topic):
    best = None
    best_size = 0
    for f in glob.glob(os.path.join(JSON_DIR, '*.json')):
        try:
            d = json.load(open(f, 'r', encoding='utf-8'))
            if d.get('topic') == topic:
                sz = os.path.getsize(f)
                if sz > best_size:
                    best = f
                    best_size = sz
        except:
            pass
    return best

def call_openai(prompt, max_retries=3, max_tokens=2000):
    delay = 3
    for attempt in range(max_retries):
        try:
            with SEMAPHORE:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=max_tokens
                )
            return res.choices[0].message.content
        except Exception as e:
            print(f"    [Retry {attempt+1}]: {e}")
            time.sleep(delay)
            delay *= 2
    return "ERROR"

def run():
    print("=" * 70)
    print("ABLATION 2: Multi-agent RAG (NO Self-Evaluation)")
    print("Reuses knowledge base — OpenAI only, no Gemini")
    print("=" * 70)
    
    for idx, topic in enumerate(TOPICS, 1):
        output_file = os.path.join(OUTPUT_DIR, f"{topic}.json")
        if os.path.exists(output_file):
            print(f"\n[{idx}/10] {topic} — SKIP")
            continue
        
        print(f"\n[{idx}/10] {topic}")
        
        src = find_best_json(topic)
        if not src:
            print(f"  ✗ No source JSON")
            continue
        
        d = json.load(open(src, 'r', encoding='utf-8'))
        refs = d.get('references', [])
        book = d.get('book_vi') or d.get('ui_book') or {}
        proposed_chapters = book.get('chapters', [])
        
        start = time.time()
        
        # === Step 1: Extract passages text from proposed book ===
        all_passages = {}
        for ch in proposed_chapters:
            for sec in ch.get('sections', []):
                content = sec.get('content', '')
                clean = re.sub(r'<[^>]+>', '', content)
                # Extract cited passage IDs
                cited_ids = re.findall(r'\[(\d+)\]', clean)
                for cid in cited_ids:
                    if cid not in all_passages:
                        all_passages[cid] = clean[:500]
        
        ref_context = "\n".join([f"[{r.get('id','')}] {r.get('title','')}" for r in refs])
        
        # === Step 2: Multi-agent Outline (Agent 1: Term Extractor) ===
        print(f"  → Agent 1: Term Extraction...")
        terms_prompt = f"""Trích xuất 30-50 thuật ngữ khoa học cốt lõi cho chủ đề "{topic}" 
từ danh sách tài liệu: {ref_context[:3000]}
Trả về JSON: {{"core_terms": ["term1", "term2", ...], "supporting_terms": ["s1", "s2", ...]}}"""
        
        terms_raw = call_openai(terms_prompt, max_tokens=1000)
        try:
            terms_clean = re.sub(r'^```(?:json)?\s*', '', terms_raw.strip(), flags=re.IGNORECASE)
            terms_clean = re.sub(r'\s*```$', '', terms_clean.strip())
            terms_data = json.loads(terms_clean)
        except:
            terms_data = {"core_terms": [topic], "supporting_terms": []}
        
        all_terms = terms_data.get("core_terms", []) + terms_data.get("supporting_terms", [])
        print(f"    → {len(all_terms)} terms extracted")
        
        # === Step 3: Agent 2: Outline Builder ===
        print(f"  → Agent 2: Outline Generation...")
        outline_prompt = f"""Dựa trên thuật ngữ sau, tạo dàn ý giáo trình chuyên sâu cho "{topic}".

Thuật ngữ: {', '.join(all_terms[:40])}

Nguồn tài liệu: {ref_context[:2000]}

YÊU CẦU:
- 8-12 chương, mỗi chương 3-5 mục
- Tên chương/mục KHÔNG ĐƯỢC trùng lặp
- Sắp xếp từ cơ bản → nâng cao
- Mỗi section phải có recommended_pids (danh sách ID nguồn liên quan)

Trả về JSON: {{"outline": [{{"title": "Chương", "sections": [{{"title": "Mục", "recommended_pids": ["1","2"]}}]}}]}}"""
        
        outline_raw = call_openai(outline_prompt, max_tokens=3000)
        try:
            outline_clean = re.sub(r'^```(?:json)?\s*', '', outline_raw.strip(), flags=re.IGNORECASE)
            outline_clean = re.sub(r'\s*```$', '', outline_clean.strip())
            outline_data = json.loads(outline_clean)
        except:
            outline_data = {"outline": [{"title": topic, "sections": [{"title": "Tổng quan", "recommended_pids": []}]}]}
        
        raw_outline = outline_data.get("outline", [])
        print(f"    → {len(raw_outline)} chapters")
        
        # === Step 4: Agent 3: Multi-agent Parallel Section Writing ===
        print(f"  → Agent 3: Multi-agent Section Writing...")
        
        def write_section(ch_title, sec_title, sec_pids):
            # Find relevant passages
            context_bits = []
            for pid in sec_pids[:5]:
                for ref in refs:
                    if str(ref.get('id','')) == str(pid):
                        context_bits.append(f"[{pid}] {ref.get('title', '')}")
            
            if not context_bits:
                context_bits = [f"[{r.get('id','')}] {r.get('title','')}" for r in refs[:5]]
            
            prompt = f"""Viết nội dung chi tiết cho mục "{sec_title}" trong chương "{ch_title}" 
của giáo trình "{topic}".

NGUỒN:
{chr(10).join(context_bits)}

YÊU CẦU:
- 300-500 từ
- PHẢI trích dẫn [id] inline
- Khoa học, chuẩn đại học
- Không bịa ngoài nguồn"""
            
            return call_openai(prompt, max_tokens=1500)
        
        final_chapters = []
        for ch_idx, chap in enumerate(raw_outline):
            ch_title = chap.get("title", f"Chương {ch_idx+1}")
            sections = chap.get("sections", [])
            
            ch_sections = []
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {}
                for sec in sections:
                    s_title = sec.get("title", "") if isinstance(sec, dict) else str(sec)
                    s_pids = sec.get("recommended_pids", []) if isinstance(sec, dict) else []
                    f = executor.submit(write_section, ch_title, s_title, s_pids)
                    futures[f] = s_title
                
                for f in as_completed(futures, timeout=120):
                    s_title = futures[f]
                    try:
                        content = f.result()
                        ch_sections.append({"title": s_title, "content": content})
                    except Exception as e:
                        ch_sections.append({"title": s_title, "content": f"[Error: {e}]"})
            
            final_chapters.append({"title": ch_title, "sections": ch_sections})
            print(f"    ✓ Ch {ch_idx+1}/{len(raw_outline)}: {len(ch_sections)} secs")
            time.sleep(1)
        
        # === Step 5: NO AUDIT (ablation — skip ScholarlyAuditEngine) ===
        print(f"  → SKIP Audit (ablation)")
        
        elapsed = time.time() - start
        
        output = {
            "topic": topic,
            "method": "multiagent_no_self_eval",
            "book_vi": {"title": f"Giáo trình {topic}", "chapters": final_chapters},
            "references": refs,
            "terms": all_terms,
            "elapsed_seconds": elapsed
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        total_secs = sum(len(c.get("sections", [])) for c in final_chapters)
        print(f"  ✓ Done {elapsed:.0f}s — {len(final_chapters)} ch, {total_secs} sec")
        time.sleep(3)

if __name__ == "__main__":
    run()
    print("\n✅ Ablation 2 hoàn tất!")
