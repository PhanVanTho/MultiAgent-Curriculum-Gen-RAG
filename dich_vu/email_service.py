# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import logging
from cau_hinh import CauHinh

logger = logging.getLogger("app.email_service")

def gui_email_otp(to_email, otp):
    """
    Gửi email chứa mã OTP đến địa chỉ email người nhận.
    Nếu cấu hình SMTP không khả dụng hoặc bị thiếu credentials, sẽ tự động
    chuyển sang ghi nhận vào hệ thống logs (Mock/Fallback).
    """
    username = CauHinh.MAIL_USERNAME
    password = CauHinh.MAIL_PASSWORD
    server_host = CauHinh.MAIL_SERVER
    port = CauHinh.MAIL_PORT
    use_tls = CauHinh.MAIL_USE_TLS
    sender = CauHinh.MAIL_DEFAULT_SENDER or username

    subject = "[Giáo Trình AI] Mã xác thực OTP đăng ký tài khoản"
    body = f"""Chào bạn,

Bạn đang thực hiện đăng ký tài khoản trên hệ thống Biên soạn Giáo Trình AI.
Mã xác thực OTP của bạn là:

===========================
         {otp}
===========================

Mã xác thực này có thời hạn sử dụng là 5 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.

Trân trọng,
Đội ngũ phát triển Giáo Trình AI.
"""

    # Check if SMTP details are missing
    if not username or not password:
        logger.warning(f"==================================================")
        logger.warning(f"[EMAIL MOCK] Gửi OTP đến: {to_email}")
        logger.warning(f"[EMAIL MOCK] Mã xác thực OTP: {otp}")
        logger.warning(f"==================================================")
        print(f"\n[EMAIL MOCK] Gửi OTP đến: {to_email} | Mã OTP: {otp}\n", flush=True)
        return True, "Chế độ Mô phỏng (Mock): Mã OTP đã được in ra log/console."

    try:
        # Create message container
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender
        msg['To'] = to_email

        # Connect to server
        if use_tls:
            server = smtplib.SMTP(server_host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(server_host, port, timeout=10)

        server.login(username, password)
        server.sendmail(sender, [to_email], msg.as_string())
        server.quit()
        
        logger.info(f"Đã gửi email OTP thành công tới: {to_email}")
        return True, "Mã OTP đã được gửi tới email của bạn."
        
    except Exception as e:
        error_msg = f"Lỗi gửi email SMTP: {str(e)}"
        logger.error(error_msg)
        # Fallback to log the OTP so registration flow does not break if SMTP server blocks
        logger.warning(f"==================================================")
        logger.warning(f"[EMAIL FALLBACK/LỖI SMTP] Gửi OTP đến: {to_email}")
        logger.warning(f"[EMAIL FALLBACK/LỖI SMTP] Mã xác thực OTP: {otp}")
        logger.warning(f"==================================================")
        print(f"\n[EMAIL FALLBACK/LỖI SMTP] Gửi OTP đến: {to_email} | Mã OTP: {otp}\n", flush=True)
        return False, f"Không gửi được mail thật (Lỗi SMTP). Hệ thống đã tự động ghi nhận mã OTP vào log: {otp}"

def gui_email_xoa_tai_khoan(admin_email, account_info):
    """
    Gửi thông báo yêu cầu xóa tài khoản đến email của admin.
    account_info: dict chứa tên đăng nhập, email, lý do, ghi chú.
    """
    username = CauHinh.MAIL_USERNAME
    password = CauHinh.MAIL_PASSWORD
    server_host = CauHinh.MAIL_SERVER
    port = CauHinh.MAIL_PORT
    use_tls = CauHinh.MAIL_USE_TLS
    sender = CauHinh.MAIL_DEFAULT_SENDER or username

    subject = "[Giáo Trình AI] Yêu cầu xóa tài khoản người dùng"
    body = f"""Chào Admin,

Hệ thống vừa nhận được yêu cầu xóa tài khoản từ người dùng với thông tin như sau:

- Tên đăng nhập: {account_info.get('username', 'N/A')}
- Email đăng ký: {account_info.get('email', 'N/A')}
- Lý do yêu cầu xóa: {account_info.get('reason', 'N/A')}
- Ghi chú thêm: {account_info.get('notes', 'N/A')}

Vui lòng kiểm tra và thực hiện xử lý yêu cầu xóa tài khoản này trong hệ thống.

Trân trọng,
Hệ thống Biên soạn Giáo Trình AI.
"""

    if not username or not password:
        logger.warning(f"==================================================")
        logger.warning(f"[EMAIL MOCK] Gửi yêu cầu xóa tài khoản đến admin: {admin_email}")
        logger.warning(f"[EMAIL MOCK] Thông tin: {account_info}")
        logger.warning(f"==================================================")
        print(f"\n[EMAIL MOCK] Gửi yêu cầu xóa tài khoản đến: {admin_email} | Thông tin: {account_info}\n", flush=True)
        return True, "Chế độ Mô phỏng (Mock): Yêu cầu đã được ghi nhận vào logs."

    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender
        msg['To'] = admin_email

        if use_tls:
            server = smtplib.SMTP(server_host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(server_host, port, timeout=10)

        server.login(username, password)
        server.sendmail(sender, [admin_email], msg.as_string())
        server.quit()
        
        logger.info(f"Đã gửi email thông báo xóa tài khoản tới admin: {admin_email}")
        return True, "Yêu cầu xóa tài khoản đã được gửi tới Ban quản trị."
    except Exception as e:
        error_msg = f"Lỗi gửi email xóa tài khoản SMTP: {str(e)}"
        logger.error(error_msg)
        logger.warning(f"==================================================")
        logger.warning(f"[EMAIL FALLBACK/LỖI SMTP] Gửi yêu cầu xóa tài khoản đến: {admin_email}")
        logger.warning(f"[EMAIL FALLBACK/LỖI SMTP] Thông tin: {account_info}")
        logger.warning(f"==================================================")
        print(f"\n[EMAIL FALLBACK/LỖI SMTP] Gửi yêu cầu xóa tài khoản đến: {admin_email} | Thông tin: {account_info}\n", flush=True)
        return False, f"Lỗi gửi email thực tế (SMTP): {str(e)}. Thông tin yêu cầu đã được ghi nhận vào logs."


def gui_email_support_ticket(admin_email, ticket_info):
    """
    Gửi thông báo yêu cầu hỗ trợ đến email của admin.
    ticket_info: dict chứa họ tên, email, tiêu đề, nội dung tin nhắn.
    """
    username = CauHinh.MAIL_USERNAME
    password = CauHinh.MAIL_PASSWORD
    server_host = CauHinh.MAIL_SERVER
    port = CauHinh.MAIL_PORT
    use_tls = CauHinh.MAIL_USE_TLS
    sender = CauHinh.MAIL_DEFAULT_SENDER or username

    subject = f"[Giáo Trình AI] Yêu cầu hỗ trợ mới: {ticket_info.get('subject', 'N/A')}"
    body = f"""Chào Admin,

Hệ thống vừa nhận được một yêu cầu hỗ trợ mới từ người dùng với thông tin như sau:

- Họ và tên: {ticket_info.get('name', 'N/A')}
- Email liên hệ: {ticket_info.get('email', 'N/A')}
- Tiêu đề: {ticket_info.get('subject', 'N/A')}
- Nội dung tin nhắn:
{ticket_info.get('message', 'N/A')}

Vui lòng kiểm tra và liên hệ phản hồi người dùng sớm nhất có thể.

Trân trọng,
Hệ thống Biên soạn Giáo Trình AI.
"""

    if not username or not password:
        logger.warning(f"==================================================")
        logger.warning(f"[EMAIL MOCK] Nhận yêu cầu hỗ trợ gửi đến admin: {admin_email}")
        logger.warning(f"[EMAIL MOCK] Thông tin hỗ trợ: {ticket_info}")
        logger.warning(f"==================================================")
        print(f"\n[EMAIL MOCK] Nhận yêu cầu hỗ trợ đến: {admin_email} | Thông tin: {ticket_info}\n", flush=True)
        return True, "Chế độ Mô phỏng (Mock): Yêu cầu hỗ trợ đã được gửi thành công."

    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender
        msg['To'] = admin_email

        if use_tls:
            server = smtplib.SMTP(server_host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(server_host, port, timeout=10)

        server.login(username, password)
        server.sendmail(sender, [admin_email], msg.as_string())
        server.quit()
        
        logger.info(f"Đã gửi email yêu cầu hỗ trợ tới admin: {admin_email}")
        return True, "Yêu cầu hỗ trợ đã được gửi tới Ban quản trị."
    except Exception as e:
        error_msg = f"Lỗi gửi email hỗ trợ SMTP: {str(e)}"
        logger.error(error_msg)
        logger.warning(f"==================================================")
        logger.warning(f"[EMAIL FALLBACK/LỖI SMTP] Gửi yêu cầu hỗ trợ đến: {admin_email}")
        logger.warning(f"[EMAIL FALLBACK/LỖI SMTP] Thông tin hỗ trợ: {ticket_info}")
        logger.warning(f"==================================================")
        print(f"\n[EMAIL FALLBACK/LỖI SMTP] Gửi yêu cầu hỗ trợ đến: {admin_email} | Thông tin: {ticket_info}\n", flush=True)
        return False, f"Lỗi gửi email thực tế (SMTP): {str(e)}. Thông tin yêu cầu đã được ghi nhận vào logs."


def gui_email_thanh_toan_thanh_cong(to_email, username, so_token, so_tien, ma_giao_dich, phuong_thuc):
    """
    Gửi email thông báo nạp token thành công đến người dùng và quản trị viên.
    """
    username_smtp = CauHinh.MAIL_USERNAME
    password_smtp = CauHinh.MAIL_PASSWORD
    server_host = CauHinh.MAIL_SERVER
    port = CauHinh.MAIL_PORT
    use_tls = CauHinh.MAIL_USE_TLS
    sender = CauHinh.MAIL_DEFAULT_SENDER or username_smtp
    admin_email = CauHinh.ADMIN_NOTIFICATION_EMAIL

    subject_user = f"[Giáo Trình AI] Nạp token thành công - Giao dịch {ma_giao_dich}"
    body_user = f"""Chào {username},

Bạn đã nạp thành công {so_token} token vào tài khoản.
Thông tin chi tiết giao dịch:
- Mã giao dịch: {ma_giao_dich}
- Phương thức thanh toán: {phuong_thuc}
- Số tiền thanh toán: {so_tien:,.0f} VND
- Số token nhận được: {so_token} token

Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi!

Trân trọng,
Đội ngũ phát triển Giáo Trình AI.
"""

    subject_admin = f"[Giáo Trình AI - Admin] Giao dịch nạp token thành công - {ma_giao_dich}"
    body_admin = f"""Chào Admin,

Hệ thống ghi nhận giao dịch nạp token thành công mới:
- Tài khoản người dùng: {username}
- Email đăng ký: {to_email}
- Mã giao dịch: {ma_giao_dich}
- Phương thức: {phuong_thuc}
- Số tiền thanh toán: {so_tien:,.0f} VND
- Số token nạp: {so_token} token

Trân trọng,
Hệ thống Biên soạn Giáo Trình AI.
"""

    # Mock fallback if SMTP is missing
    if not username_smtp or not password_smtp:
        logger.warning("==================================================")
        logger.warning(f"[EMAIL MOCK] Giao dịch nạp token thành công: {ma_giao_dich}")
        logger.warning(f"[EMAIL MOCK] Gửi tới User: {to_email} | Admin: {admin_email}")
        logger.warning(f"[EMAIL MOCK] Số tiền: {so_tien:,.0f} VND | Token: {so_token}")
        logger.warning("==================================================")
        print(f"\n[EMAIL MOCK] Nạp token thành công! User: {to_email} | Admin: {admin_email} | Mã GD: {ma_giao_dich}\n", flush=True)
        return True

    # Helper function to send single email
    def send_one(recipient, subject, body):
        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = sender
            msg['To'] = recipient

            if use_tls:
                server = smtplib.SMTP(server_host, port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(server_host, port, timeout=10)

            server.login(username_smtp, password_smtp)
            server.sendmail(sender, [recipient], msg.as_string())
            server.quit()
            logger.info(f"Đã gửi email giao dịch thành công tới: {recipient}")
            return True
        except Exception as e:
            logger.error(f"Lỗi gửi email giao dịch tới {recipient}: {e}")
            return False

    # Send to User
    if to_email:
        send_one(to_email, subject_user, body_user)

    # Send to Admin
    if admin_email:
        send_one(admin_email, subject_admin, body_admin)

    return True



