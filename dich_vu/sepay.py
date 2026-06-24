import requests
import re
from cau_hinh import CauHinh

SEPAY_BASE_URL = "https://my.sepay.vn/userapi/transactions/list"

def encode_payment_id(p_id: int) -> str:
    """Mã hóa ID hóa đơn thành chuỗi HEX dùng phép XOR"""
    return hex(p_id ^ CauHinh.SEPAY_XOR_KEY)[2:].upper()

def decode_payment_id(hex_str: str) -> int:
    """Giải mã chuỗi HEX thành ID hóa đơn"""
    return int(hex_str, 16) ^ CauHinh.SEPAY_XOR_KEY

def get_last_transactions(limit: int = 20) -> list:
    """
    Gọi API SePay để lấy danh sách giao dịch ngân hàng mới nhất.
    """
    if not CauHinh.SEPAY_API_KEY:
        print("Loi: Chua cau hinh SEPAY_API_KEY")
        return []
        
    headers = {
        "Authorization": f"Bearer {CauHinh.SEPAY_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        "account_number": CauHinh.SEPAY_ACCOUNT_NUMBER,
        "limit": limit
    }
    
    try:
        response = requests.get(SEPAY_BASE_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("transactions", [])
    except requests.RequestException as e:
        print(f"Loi goi SePay API: {e}")
        return []

def check_sepay_transactions(payment_id: int, expected_amount: int) -> bool:
    """
    Kiểm tra xem giao dịch cho `payment_id` đã được thanh toán chưa.
    Duyệt qua danh sách giao dịch SePay và so khớp regex.
    """
    target_hex = encode_payment_id(payment_id)
    prefix = CauHinh.SEPAY_WEB_NAME + "NAPTOKEN"
    pattern = rf"{prefix}([A-Fa-f0-9]+)"
    
    history = get_last_transactions()
    
    for tx in history:
        content = tx.get('transaction_content') or tx.get('content') or ''
        amount = float(tx.get('amount_in', 0))
        
        # Bóc tách mã HEX từ nội dung chuyển khoản
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            found_hex = match.group(1).upper()
            if found_hex == target_hex and amount >= expected_amount:
                # Giao dịch trùng khớp mã nạp và số tiền đủ
                return True
                
    return False
