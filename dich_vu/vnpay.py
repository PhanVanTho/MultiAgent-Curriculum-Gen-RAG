import hashlib
import hmac
import urllib.parse
from datetime import datetime

class VNPay:
    # Force server reload: updated local VNPAY logo asset
    def __init__(self, tmn_code: str, hash_secret: str, payment_url: str):
        self.tmn_code = tmn_code
        self.hash_secret = hash_secret
        self.payment_url = payment_url

    def create_payment_url(self, txn_ref: str, amount: int, order_info: str, return_url: str, ip_addr: str) -> str:
        """Tạo đường dẫn chuyển hướng thanh toán VNPAY."""
        # Clean IP address to prevent comma-separated list or IPv6 local formats
        if not ip_addr:
            ip_addr = "118.70.194.200"
        else:
            ip_addr = ip_addr.split(",")[0].strip()
            if ip_addr in ("::1", "127.0.0.1"):
                ip_addr = "118.70.194.200"
            # If it's a general IPv6 or invalid format, we default to a standard public IP
            if ":" in ip_addr:
                ip_addr = "118.70.194.200"

        params = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": self.tmn_code,
            "vnp_Amount": str(amount * 100),  # VNPAY yêu cầu nhân 100 (đơn vị: vnđ)
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": str(txn_ref),
            "vnp_OrderInfo": order_info,
            "vnp_OrderType": "billpayment",
            "vnp_Locale": "vn",
            "vnp_ReturnUrl": return_url,
            "vnp_IpAddr": ip_addr,
            "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S")
        }
        
        # Sắp xếp các tham số theo bảng chữ cái A-Z
        sorted_params = sorted(params.items())
        
        # Xây dựng chuỗi hash_data (sử dụng urllib.parse.quote để spaces thành %20, chuẩn VNPay 2.1.0)
        hash_data = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)
        
        # Tính toán HMAC-SHA512 chữ ký số bảo mật
        secure_hash = hmac.new(
            self.hash_secret.encode('utf-8'),
            hash_data.encode('utf-8'),
            hashlib.sha512
        ).hexdigest().upper()
        
        try:
            with open("vnpay_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n=== VNPAY REQUEST DATA ===\n")
                f.write(f"Hash Secret: {self.hash_secret}\n")
                f.write(f"Hash Data Raw String: {hash_data}\n")
                f.write(f"Secure Hash: {secure_hash}\n")
                f.write(f"===========================\n")
        except Exception as log_err:
            print(f"Loi ghi log: {log_err}")
            
        return f"{self.payment_url}?{hash_data}&vnp_SecureHash={secure_hash}"

    def verify_payment(self, response_params: dict) -> bool:
        """Xác thực tính toàn vẹn của dữ liệu phản hồi từ VNPAY."""
        secure_hash = response_params.get("vnp_SecureHash")
        if not secure_hash:
            return False
            
        # Lọc ra các tham số bắt đầu bằng vnp_ và không chứa trường hash, bỏ qua các giá trị rỗng
        hash_params = {
            k: v for k, v in response_params.items()
            if k.startswith("vnp_") and k not in ("vnp_SecureHash", "vnp_SecureHashType") and v != ""
        }
        
        # Sắp xếp các tham số theo thứ tự bảng chữ cái
        sorted_params = sorted(hash_params.items())
        
        # Xây dựng chuỗi hash_data để đối soát (sử dụng quote_via=urllib.parse.quote để spaces thành %20, chuẩn VNPay 2.1.0)
        hash_data = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)
        
        # Tính toán chữ ký kiểm tra
        computed_hash = hmac.new(
            self.hash_secret.encode('utf-8'),
            hash_data.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        # So khớp chữ ký sử dụng phương thức so sánh an toàn timing attacks
        return hmac.compare_digest(computed_hash.lower(), secure_hash.lower())
