# MultiAgent-Curriculum-Gen-RAG

Hệ thống sinh giáo trình đại học tự động dựa trên kiến trúc Đa tác tử (Multi-agent) và RAG thích nghi (Adaptive RAG).

## 🌟 Tính năng cốt lõi
- **EKRE (Adaptive Knowledge Retrieval Engine):** Tự động thu thập và sàng lọc tri thức từ Wikipedia với cơ chế Data Sufficiency Gate.
- **Multi-agent Orchestration:** Phối hợp giữa các tác tử chuyên biệt (Safety, Discovery, Planning, Micro-Writer, Scholarly Audit).
- **Scholarly Audit (Self-Eval):** Vòng lặp phản biện chéo giữa các LLM để triệt tiêu ảo giác tri thức (Hallucination) và đảm bảo tính trung thực (Faithfulness).
- **Đánh giá định lượng:** Bộ công cụ đánh giá 6 chỉ số (RP, CR, F, AC, SC, GS) dựa trên mã nguồn Python xác định.

## 🏗️ Kiến trúc Hệ thống
1. **Adaptive Knowledge Discovery:** Kiểm định an toàn và xây dựng Knowledge Base.
2. **Structural Planning:** Quy hoạch dàn ý đa tầng theo tiến trình sư phạm.
3. **Micro-Writer:** Biên soạn song song cấp độ đoạn văn với cơ chế Self-Rescue.
4. **Scholarly Audit:** Chỉnh sửa vi phẫu (Surgical Rewrite) dựa trên bằng chứng nguồn.

## 🚀 Hướng dẫn cài đặt
1. Clone repository:
   ```bash
   git clone https://github.com/PhanVanTho/MultiAgent-Curriculum-Gen-RAG.git
   cd MultiAgent-Curriculum-Gen-RAG
   ```
2. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```
3. Cấu hình biến môi trường:
   Tạo file `.env` và điền các API Key:
   ```env
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEYS=key1,key2,key3
   ```
4. Chạy ứng dụng:
   ```bash
   python ung_dung.py
   ```

## 📊 Thực nghiệm & Đánh giá (Ablation Study)
Các script thực nghiệm phục vụ paper nằm trong thư mục gốc:
- `sinh_baseline.py`: Tạo dữ liệu Zero-shot và Vanilla RAG.
- `sinh_ablation_adaptive_rag.py`: Đánh giá Adaptive RAG (chỉ có EKRE).
- `sinh_ablation_multiagent_no_audit.py`: Đánh giá Đa tác tử không có kiểm toán.
- `danh_gia_6_cong_thuc.py`: Công cụ chấm điểm định lượng 6 chỉ số.

## 📝 Trích dẫn (Citation)
Nếu bạn sử dụng mã nguồn này trong nghiên cứu của mình, vui lòng trích dẫn:
... [Thông tin paper của bạn] ...
