# 📘 HƯỚNG DẪN CÀI ĐẶT & CẤU HÌNH HỆ THỐNG AI DATA AGGREGATOR
## Hệ thống sinh giáo trình Đại học tự động (Multi-Agent & Adaptive RAG)

Tài liệu này hướng dẫn chi tiết các bước chuẩn bị môi trường, cài đặt các phụ thuộc, cấu hình dịch vụ bên thứ ba, thiết lập cơ sở dữ liệu và vận hành hệ thống **MultiAgent-Curriculum-Gen-RAG**.

---

## 🏗️ 1. Sơ đồ Kiến trúc & Luồng xử lý Hệ thống

Để hiểu cách hoạt động trước khi cài đặt, dưới đây là luồng tương tác giữa các thành phần cốt lõi:

```mermaid
graph TD
    User([Người dùng]) -->|1. Yêu cầu tạo chủ đề / Custom chương| WebUI[Giao diện Flask Web App]
    WebUI -->|2. Khởi tạo Pipeline| Core[Động cơ Multi-Agent RAG]
    
    subgraph Multi-Agent Engine
        Core -->|3. Kiểm duyệt| Safety[Safety Router - 3-Layer Check]
        Safety -->|4. Tìm kiếm| EKRE[EKRE Discovery Engine - Wiki API]
        EKRE -->|5. Sắp xếp & Trích xuất| Planner[AI Planning - Dàn ý & Thuật ngữ]
        Planner -->|6. Viết nội dung| Writer[Micro-Writer - OpenAI Parallel]
        Writer -->|7. Đánh giá kiểm toán| Supervisor[Gemini Supervisor - Lọc ảo giác]
    end

    Core -->|8. Lưu trữ dữ liệu| DB[(Hệ thống Database: SQLite / MongoDB)]
    Core -->|9. Đóng gói tài liệu| DocGen[Xuất bản DOCX & PDF]
    DocGen -->|10. Upload Cloud| Azure[Azure Blob Storage]
    
    subgraph Dịch vụ bên thứ ba (API)
        Safety & Planner & Writer -.->|OpenAI API| OpenAI[OpenAI Services]
        EKRE & Supervisor -.->|Gemini API| Gemini[Google AI Studio]
        WebUI -.->|Ví điện tử / Ngân hàng| Payment[VNPay & SePay Gateways]
    end
```

---

## 💻 2. Yêu cầu hệ thống tối thiểu
- **Hệ điều hành**: Windows 10/11, macOS, hoặc Linux (Ubuntu 20.04+).
- **Python**: Phiên bản **3.9** trở lên (Khuyến nghị **3.10** hoặc **3.11**).
- **Cơ sở dữ liệu** (chọn 1 trong 2 cấu hình ở tệp `.env`):
  - **SQLite**: Không cần cài đặt thêm phần mềm bên ngoài (Mặc định dùng chế độ phát triển ngoại tuyến).
  - **MongoDB**: Yêu cầu cài đặt MongoDB Server cục bộ hoặc sử dụng MongoDB Atlas.

---

## 🚀 3. Các bước cài đặt chi tiết

### Bước 3.1: Tải mã nguồn về máy
Mở terminal (PowerShell trên Windows hoặc Terminal trên Linux/macOS) và chạy lệnh:
```bash
git clone https://github.com/PhanVanTho/MultiAgent-Curriculum-Gen-RAG.git
cd MultiAgent-Curriculum-Gen-RAG
```

### Bước 3.2: Khởi tạo và kích hoạt môi trường ảo (Virtual Environment)
Việc sử dụng môi trường ảo giúp cô lập các thư viện của dự án, tránh xung đột hệ thống.

- **Trên Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **Trên Linux / macOS**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Bước 3.3: Cài đặt các thư viện phụ thuộc
Cài đặt toàn bộ các thư viện được liệt kê trong tệp `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ 4. Hướng dẫn cấu hình biến môi trường (`.env`)

Hãy sao chép tệp `.env.example` thành tệp `.env` ở thư mục gốc của dự án:
```bash
# Windows
copy .env.example .env
# Linux / macOS
cp .env.example .env
```

Sau đó, chỉnh sửa các tham số trong tệp `.env` theo thông tin chi tiết dưới đây:

### 4.1 Cấu hình Cốt lõi & Trí tuệ Nhân tạo (LLM APIs)
| Tên Biến | Giá trị Khuyến nghị / Mô tả |
| :--- | :--- |
| `FLASK_SECRET_KEY` | Một chuỗi ngẫu nhiên bất kỳ dùng để mã hóa Session cookie của Flask. |
| `OPENAI_API_KEY` | Khóa API từ OpenAI (định dạng `sk-proj-...`). Dùng để phân loại an toàn, lập dàn ý, và viết bài. |
| `OPENAI_MODEL` | `gpt-4o-mini` (Model chính để viết nội dung tiết kiệm chi phí). |
| `SEARCH_MODEL` | `gpt-4o` (Model thông minh hơn dùng để xác định thực thể cốt lõi). |
| `GEMINI_API_KEYS` | Chuỗi danh sách khóa API của Google AI Studio cách nhau bởi dấu phẩy (Ví dụ: `key1,key2,key3`). Hỗ trợ xoay vòng khóa tự động tránh lỗi giới hạn tần suất (429 Rate Limit). |
| `GEMINI_MODEL` | `gemini-2.5-flash` (Model giám sát chính). |
| `SUPERVISOR_MODEL_LITE` | `gemini-3.1-flash-lite` (Dùng cho giám sát tốc độ cao và chi phí thấp). |

### 4.2 Cấu hình Cơ sở dữ liệu (Database)
Hệ thống sử dụng bộ điều phối thích ứng linh hoạt. Bạn có thể bật SQLite hoặc MongoDB:
- **Chế độ SQLite (Khuyên dùng cho chạy thử nhanh)**:
  ```env
  DB_USE_SQLITE=True
  ```
- **Chế độ MongoDB (Khuyên dùng cho môi trường sản phẩm thực tế)**:
  ```env
  DB_USE_SQLITE=False
  DB_TYPE=mongodb
  MONGO_URI="mongodb://localhost:27017/giao_trinh_ai"
  ```

### 4.3 Cấu hình Cổng thanh toán (Thanh toán tự động nâng cao)
Hệ thống tích hợp sẵn VNPay (Cổng thanh toán Sandbox) và SePay (Quét mã QR tự động cập nhật token):
```env
# Trạng thái kích hoạt cổng thanh toán
PAYMENT_VNPAY_ACTIVE=True
PAYMENT_SEPAY_ACTIVE=True

# VNPay Sandbox
VNPAY_TMN_CODE="MÃ_TMN_CỦA_BẠN"
VNPAY_HASH_SECRET="CHUỖI_BẢO_MẬT_VNPAY"
VNPAY_PAYMENT_URL="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNPAY_RETURN_URL="http://127.0.0.1:5000/payment/callback"

# SePay cấu hình quét mã QR chuyển khoản ngân hàng
SEPAY_API_KEY="KEY_API_SEPAY"
SEPAY_ACCOUNT_NUMBER="SỐ_TÀI_KHOẢN_NHẬN_TIỀN"
SEPAY_BANK_BRAND="MBBank" # Hoặc Vietinbank, VCB...
```

### 4.4 Cấu hình Lưu trữ Đám mây (Azure Blob Storage)
Để các tệp tài liệu xuất bản (.docx, .pdf) không bị mất khi deploy lên các nền tảng server không lưu trữ lâu dài (như Heroku), cấu hình Azure Storage:
```env
AZURE_STORAGE_CONNECTION_STRING="Chuỗi kết nối Azure Storage Account của bạn"
AZURE_BLOB_CONTAINER_NAME="giao-trinh-ai-files"
```

### 4.5 Cấu hình Gửi Email (Xác thực & Thông báo)
Dùng để gửi mã OTP khi đăng ký hoặc quên mật khẩu qua giao thức SMTP (Gmail):
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME="email_gui_thu@gmail.com"
MAIL_PASSWORD="mat_khau_ung_dung_gmail" # Mật khẩu ứng dụng 16 ký tự của Google
MAIL_DEFAULT_SENDER="email_gui_thu@gmail.com"
```

---

## 🏃 5. Vận hành hệ thống

### 5.1 Khởi tạo cơ sở dữ liệu ban đầu (Chỉ chạy lần đầu tiên)
Nếu bạn sử dụng SQLite hoặc MySQL (thông qua SQLAlchemy), hãy chạy lệnh sau để khởi tạo cấu trúc bảng:
```bash
flask db upgrade
```
*Lưu ý: Nếu không sử dụng migration, ứng dụng sẽ tự động tạo cấu trúc bảng khi khởi chạy tệp `ung_dung.py`.*

### 5.2 Khởi chạy Server Web giao diện người dùng
```bash
python ung_dung.py
```
Sau khi khởi chạy thành công, mở trình duyệt và truy cập địa chỉ:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 5.3 Sử dụng công cụ dòng lệnh (CLI - Không cần giao diện)
Nếu bạn muốn chạy tiến trình sinh giáo trình trực tiếp từ Terminal để test hoặc debug:
```bash
python cli.py --topic "Trí Tuệ Nhân Tạo" --scale tieu_chuan --lang vi
```

---

## 🧪 6. Chạy Kiểm thử tự động (Unit Tests)

Hệ thống đi kèm bộ kiểm thử toàn diện 39 ca kiểm thử (bao gồm kiểm thử bảo mật, kiểm duyệt từ viết tắt, kiểm thử RAG, và kiểm thử thanh toán). Để kiểm tra sự ổn định của hệ thống sau khi cài đặt:

```bash
python -m unittest discover tests
```

Nếu tất cả các test case đều hiển thị `OK` ở cuối cùng, hệ thống của bạn đã cài đặt hoàn hảo và sẵn sàng vận hành.

---

## ⚠️ 7. Các lỗi thường gặp và cách xử lý (Troubleshooting)

1. **Lỗi Quota Gemini (429 Resource Exhausted)**:
   - *Cách xử lý*: Cấu hình thêm nhiều API Key trong biến `GEMINI_API_KEYS` ở tệp `.env` cách nhau bằng dấu phẩy để kích hoạt cơ chế tự động xoay vòng khóa (API Key rotation) của hệ thống.
2. **Lỗi Không tải được PDF/DOCX**:
   - *Cách xử lý*: Đảm bảo bạn đã cài đặt công cụ tạo PDF (như `weasyprint` hoặc thư viện liên quan) và chuỗi cấu hình `AZURE_STORAGE_CONNECTION_STRING` là chính xác nếu đang sử dụng chế độ lưu trữ đám mây.
3. **Lỗi SSL Handshake khi cào dữ liệu Wikipedia**:
   - *Cách xử lý*: Kiểm tra kết nối mạng của bạn. Wikipedia đôi khi chặn các IP thuộc dải cloud hosting thông dụng, chạy trên máy cá nhân hoặc cài thêm VPN nếu cần thiết.

---
*Chúc bạn cài đặt và trải nghiệm thành công Hệ thống biên soạn giáo trình AI!*
