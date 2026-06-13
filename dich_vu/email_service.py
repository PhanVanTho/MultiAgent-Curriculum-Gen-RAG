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
