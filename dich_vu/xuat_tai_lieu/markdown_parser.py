# -*- coding: utf-8 -*-
import markdown
import re

def parse_markdown(text):
    """
    Biên dịch Markdown sang HTML một cách an toàn.
    Sử dụng thư viện 'markdown' của Python.
    """
    if not text:
        return ""
    
    # 1. Tiền xử lý: Escape các thẻ HTML có sẵn trong markdown block để tránh bị parse lầm
    # Nếu text chứa ```html ... ``` hoặc `<h1>`
    # Thư viện markdown mặc định sẽ giữ nguyên HTML thuần (raw HTML).
    # Chúng ta muốn các thẻ HTML mà AI sinh ra như `<h1>` (để ví dụ) phải được hiển thị chứ không phải bị render thành h1.
    # Thư viện markdown tự động escape nội dung trong cặp backtick ` `.
    
    # Sử dụng extension 'fenced_code' để hỗ trợ block code ``` và 'nl2br' để xuống dòng
    html_output = markdown.markdown(
        text,
        extensions=['fenced_code', 'nl2br', 'sane_lists']
    )
    
    return html_output
