"""
ABLATION VARIANT 1: Adaptive RAG (EKRE-like retrieval, Single Agent)
=====================================================================
TÁI SỬ DỤNG passages từ Proposed JSON (cùng knowledge base)
Chỉ khác: 1 agent writer (không multi-agent, không audit)

Tránh gọi lại Gemini (quota exhausted) — chỉ dùng OpenAI
"""
import os, sys, json, time, re, glob
from openai import OpenAI
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OUTPUT_DIR = r"d:\tu_dong_giao_trinh\ThucNghiem_KetQua\Ablation_AdaptiveRAG"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load passages from existing Proposed JSONs
JSON_DIR = r"d:\tu_dong_giao_trinh\du_lieu\dau_ra\json"
TOPICS = [
    "Trí tuệ nhân tạo", "Biến đổi khí hậu", "Tin sinh học",
    "Tâm lý học nhận thức", "An ninh mạng", "Công nghệ chuỗi khối",
    "Xã hội học", "Công nghệ nano", "Kỹ thuật phần mềm", "Điện toán lượng tử"
]

def find_best_json(topic):
    """Find the largest JSON for a topic (best quality)"""
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

def call_openai(prompt, max_retries=5):
    delay = 5
    for attempt in range(max_retries):
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000
            )
            return res.choices[0].message.content
        except Exception as e:
            print(f"  [Retry {attempt+1}/{max_retries}]: {e}")
            time.sleep(delay)
            delay *= 2
    return "ERROR"

def run():
    print("=" * 70)
    print("ABLATION 1: Adaptive RAG (EKRE retrieval + Single Agent Writer)")
    print("Reuses passages from Proposed JSON — only OpenAI, no Gemini")
    print("=" * 70)
    
    for idx, topic in enumerate(TOPICS, 1):
        output_file = os.path.join(OUTPUT_DIR, f"{topic}.json")
        if os.path.exists(output_file):
            print(f"\n[{idx}/10] {topic} — SKIP (exists)")
            continue
        
        print(f"\n[{idx}/10] {topic}")
        
        # Load passages from Proposed
        src = find_best_json(topic)
        if not src:
            print(f"  ✗ No source JSON found")
            continue
        
        d = json.load(open(src, 'r', encoding='utf-8'))
        refs = d.get('references', [])
        
        # Build context from references
        # We use ref titles as knowledge context (since we can't re-crawl)
        context_parts = []
        for ref in refs:
            rid = ref.get('id', '')
            title = ref.get('title', '')
            url = ref.get('url', '')
            context_parts.append(f"[{rid}] {title} (source: {url})")
        
        # Also extract some text from the proposed book for reference passages
        book = d.get('book_vi') or d.get('ui_book') or {}
        chapters = book.get('chapters', [])
        passage_texts = []
        for ch in chapters[:3]:  # Take first 3 chapters as sample passages
            for sec in ch.get('sections', [])[:2]:
                content = sec.get('content', '')
                clean = re.sub(r'<[^>]+>', '', content)[:1000]
                passage_texts.append(clean)
        
        ref_context = "\n".join(context_parts)
        passage_context = "\n\n---\n".join(passage_texts[:6])[:8000]
        
        start = time.time()
        
        # Single Agent: one prompt, one call → entire curriculum
        prompt = f"""Bạn là giảng viên đại học. Dựa trên các tài liệu nguồn sau, viết giáo trình chuyên sâu cho "{topic}".

NGUỒN TÀI LIỆU (từ Wikipedia):
{ref_context}

MẪU NỘI DUNG THAM KHẢO:
{passage_context[:4000]}

YÊU CẦU:
- Chia 8-12 chương, mỗi chương 3-5 mục
- Mỗi mục viết 200-400 từ nội dung chi tiết
- PHẢI trích dẫn [id] khi dùng thông tin từ nguồn
- Trình bày khoa học, đúng chuẩn đại học

Trả về JSON:
{{"title": "Tên", "chapters": [{{"title": "Chương", "sections": [{{"title": "Mục", "content": "Nội dung [id]"}}]}}]}}"""
        
        result = call_openai(prompt)
        
        # Parse
        result_clean = re.sub(r'^```(?:json)?\s*', '', result.strip(), flags=re.IGNORECASE)
        result_clean = re.sub(r'\s*```$', '', result_clean.strip())
        
        try:
            book_data = json.loads(result_clean)
        except:
            book_data = {"title": topic, "chapters": [{"title": "Content", "sections": [{"title": topic, "content": result}]}]}
        
        elapsed = time.time() - start
        
        output = {
            "topic": topic,
            "method": "adaptive_rag_ekre_only",
            "book_vi": book_data,
            "references": refs,  # Same refs as Proposed (same EKRE retrieval)
            "elapsed_seconds": elapsed
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        chs = book_data.get("chapters", [])
        secs = sum(len(c.get("sections", [])) for c in chs)
        print(f"  ✓ {elapsed:.0f}s — {len(chs)} ch, {secs} sec")
        time.sleep(2)

if __name__ == "__main__":
    run()
    print("\n✅ Ablation 1 (Adaptive RAG) hoàn tất!")
