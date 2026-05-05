# -*- coding: utf-8 -*-
import os
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

# --- IMPORT V21.5 ENTERPRISE CLEANER ---
from dich_vu.xuat_tai_lieu.bo_loc_html import clean_for_docx as _clean_text_docx

def _set_font(run, size=13, bold=False, italic=False):
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    # Buộc font EastAsia cũng là Times New Roman (quan trọng cho tiếng Việt)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:eastAsia'), 'Times New Roman')

def _sanitize_xml_text(text):
    """Loại bỏ NULL bytes và control characters không hợp lệ trong XML."""
    if not text:
        return text
    # Loại bỏ NULL bytes
    text = text.replace('\x00', '')
    # Loại bỏ control characters (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F) nhưng giữ \t \n \r
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text

def _add_paragraph(doc, text, style=None, bold=False, italic=False, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY):
    if not text:
        return None
    
    # Làm sạch markdown kỹ hơn (dùng bộ lọc V21.5)
    text = _clean_text_docx(text)
    
    # Loại bỏ NULL bytes và control characters không hợp lệ XML
    text = _sanitize_xml_text(text)
    
    text = text.strip()
    
    if not text:
        return None

    p = doc.add_paragraph(style=style)
    p.alignment = alignment
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    
    # Thụt đầu dòng 1.27cm (chuẩn giáo trình) NẾU không phải là heading hay list
    if style is None or style == "Normal":
        p.paragraph_format.first_line_indent = Inches(0.5)

    run = p.add_run(text)
    _set_font(run, size=13, bold=bold, italic=italic)
    return p

def xuat_docx(ket_qua: dict, duong_dan_docx: str):
    """
    Xuất nội dung sách ra file DOCX chuẩn định dạng giáo trình.
    """
    book = ket_qua.get("book_vi", {})
    doc = Document()

    # --- THIẾT LẬP LỀ CHUẨN GIÁO TRÌNH (BGDĐT) ---
    # Giấy A4: 21cm x 29.7cm. Lề: Trên/Dưới 2cm, Trái 3cm (đóng gáy), Phải 2cm.
    for section in doc.sections:
        section.page_height = Cm(29.7)
        section.page_width = Cm(21.0)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)

    # --- STYLE SETUP (Optional hack if styles don't exist) ---
    # (Docx mặc định đã có Normal, Heading 1...)

    # 1. Title Page
    title = book.get("title", "GIÁO TRÌNH ĐẠI HỌC")
    
    # Khoảng trắng trên
    for _ in range(5): doc.add_paragraph()
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run(title.upper())
    _set_font(run_title, size=24, bold=True)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Tài liệu biên soạn tự động bởi hệ thống AI")
    _set_font(run_sub, size=14, italic=True)
    
    doc.add_page_break()

    # 1.5 Table of Contents (Mục Lục)
    h_toc = doc.add_heading("MỤC LỤC", level=1)
    h_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in h_toc.runs:
        _set_font(run, size=16, bold=True)
        run.font.color.rgb = RGBColor(0, 0, 0)
    
    chapters_toc = book.get("chapters", [])
    for idx, ch in enumerate(chapters_toc, 1):
        # Chapter title in TOC
        toc_chap = doc.add_paragraph()
        toc_chap.paragraph_format.space_after = Pt(6)
        run_c = toc_chap.add_run(f"CHƯƠNG {idx}: {ch.get('title','').upper()}")
        _set_font(run_c, size=13, bold=True)
        
        # Sections in TOC
        for jdx, sec in enumerate(ch.get("sections", []), 1):
            toc_sec = doc.add_paragraph()
            toc_sec.paragraph_format.space_after = Pt(2)
            toc_sec.paragraph_format.left_indent = Inches(0.5) # Indent for sections
            run_s = toc_sec.add_run(f"{idx}.{jdx}. {sec.get('title','')}")
            _set_font(run_s, size=12)
            
            # Sub-sections (Level 3) in TOC
            content = sec.get("content", "")
            if content:
                sub_idx = 1
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("### "):
                        h3_title = line[4:].strip().replace('**', '').replace('`', '')
                        # Strip HTML tags if any
                        h3_title = re.sub(r'<[^>]+>', '', h3_title)
                        
                        toc_sub = doc.add_paragraph()
                        toc_sub.paragraph_format.space_after = Pt(2)
                        toc_sub.paragraph_format.left_indent = Inches(1.0)
                        run_sub = toc_sub.add_run(f"{idx}.{jdx}.{sub_idx}. {h3_title}")
                        _set_font(run_sub, size=12, italic=True)
                        sub_idx += 1
                    elif "Câu hỏi Ôn tập" in line or "Bài tập & Ôn tập" in line:
                        clean_line = line.replace('**', '').replace('###', '').strip()
                        if clean_line in ["Câu hỏi Ôn tập", "Bài tập & Ôn tập"]:
                            toc_sub = doc.add_paragraph()
                            toc_sub.paragraph_format.space_after = Pt(2)
                            toc_sub.paragraph_format.left_indent = Inches(1.0)
                            run_sub = toc_sub.add_run(clean_line)
                            _set_font(run_sub, size=12, italic=True)

    doc.add_page_break()

    # 2. Glossary (V33: Bảng thuật ngữ có định nghĩa)
    glossary = ket_qua.get("glossary", [])
    terms = ket_qua.get("terms", [])
    if glossary:
        h1 = doc.add_heading("BẢNG THUẬT NGỮ", level=1)
        for run in h1.runs:
            _set_font(run, size=16, bold=True)
        h1.alignment = WD_ALIGN_PARAGRAPH.CENTER

        for item in glossary:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            run_term = p.add_run(f"{item.get('term', '')}: ")
            _set_font(run_term, size=13, bold=True)
            run_def = p.add_run(item.get('definition', ''))
            _set_font(run_def, size=13)
        doc.add_page_break()
    elif terms:
        # Fallback: danh sách thuật ngữ cũ (không có định nghĩa)
        h1 = doc.add_heading("DANH MỤC THUẬT NGỮ", level=1)
        for run in h1.runs:
            _set_font(run, size=16, bold=True)
        h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for i, t in enumerate(terms[:100], 1):
            term_text = f"{i}. {t.get('term','')} - {t.get('meaning','')}"
            p = doc.add_paragraph(style="List Number")
            run = p.add_run(term_text)
            _set_font(run, size=13)
        doc.add_page_break()

    # 3. Chapters
    chapters = book.get("chapters", [])
    for idx, ch in enumerate(chapters, 1):
        # Chapter Heading
        h1_text = f"CHƯƠNG {idx}: {ch.get('title','').upper()}"
        h1 = doc.add_heading(h1_text, level=1)
        h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in h1.runs:
            _set_font(run, size=16, bold=True)
            # Màu đen cho chuyên nghiệp (mặc định xanh)
            run.font.color.rgb = RGBColor(0, 0, 0) 
        
        # V33: Tóm tắt chương (Đã ẩn theo yêu cầu)
        # summary = ch.get("summary", "")
        # if summary:
        #     p_sum = doc.add_paragraph()
        #     p_sum.paragraph_format.left_indent = Inches(0.3)
        #     p_sum.paragraph_format.right_indent = Inches(0.3)
        #     p_sum.paragraph_format.space_after = Pt(12)
        #     run_label = p_sum.add_run("Tóm tắt chương: ")
        #     _set_font(run_label, size=12, bold=True, italic=True)
        #     run_text = p_sum.add_run(summary)
        #     _set_font(run_text, size=12, italic=True)

        # Sections
        for jdx, sec in enumerate(ch.get("sections", []), 1):
            # Section Heading
            h2_text = f"{idx}.{jdx}. {sec.get('title','')}"
            h2 = doc.add_heading(h2_text, level=2)
            for run in h2.runs:
                _set_font(run, size=14, bold=True)
                run.font.color.rgb = RGBColor(0, 0, 0)

            # Content
            content = sec.get("content", "")
            if content:
                sub_idx = 1
                # Tách đoạn và viết
                paras = re.split(r"\n\s*\n", content)
                for raw_para in paras:
                    if raw_para.strip():
                        clean_para = raw_para.strip()
                        
                        # V41.3: Lọc BỎ TẤT CẢ thẻ HTML (đặc biệt là <span class="citation">)
                        clean_para = re.sub(r'<[^>]+>', '', clean_para)
                        
                        # Loại bỏ các ký tự markdown thừa (bold, backticks)
                        clean_para = clean_para.replace('**', '')
                        clean_para = clean_para.replace('`', '')
                        
                        # Xử lý Links trong DOCX (V15.0)
                        clean_para = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', clean_para)
                        
                        # Xử lý list item
                        if clean_para.startswith("- ") or clean_para.startswith("* "):
                            text_clean = clean_para[2:].strip()
                            _add_paragraph(doc, text_clean, style="List Bullet")
                        elif re.match(r'^\d+\.\s', clean_para):
                            # Ordered list: "1. Item"
                            text_clean = re.sub(r'^\d+\.\s', '', clean_para).strip()
                            _add_paragraph(doc, text_clean, style="List Number")
                        elif clean_para == "---":
                            # Xử lý đường kẻ ngang (V15.0)
                            p = doc.add_paragraph()
                            p_pr = p._element.get_or_add_pPr()
                            p_pbdr = qn('w:pBdr')
                            bottom = qn('w:bottom')
                            el = p_pr.find(p_pbdr)
                            if el is None:
                                el = doc.element.makeelement(p_pbdr)
                                p_pr.append(el)
                            b = doc.element.makeelement(bottom)
                            b.set(qn('w:val'), 'single')
                            b.set(qn('w:sz'), '6')
                            b.set(qn('w:space'), '1')
                            b.set(qn('w:color'), 'auto')
                            el.append(b)
                        elif clean_para.startswith("### "):
                            # Xử lý Heading 3
                            text_clean = clean_para[4:].strip()
                            # Thêm đánh số 1.1.1.
                            text_clean = f"{idx}.{jdx}.{sub_idx}. {text_clean}"
                            sub_idx += 1
                            
                            h3 = doc.add_heading(text_clean, level=3)
                            h3.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            for run in h3.runs:
                                _set_font(run, size=13, bold=True)
                                run.font.color.rgb = RGBColor(0, 0, 0)
                        elif clean_para.strip() in ["Câu hỏi Ôn tập", "Bài tập & Ôn tập"]:
                            # Nâng cấp "Câu hỏi Ôn tập" thành Heading 3 để nổi bật
                            h3 = doc.add_heading(clean_para.strip(), level=3)
                            h3.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            for run in h3.runs:
                                _set_font(run, size=13, bold=True, italic=True)
                                run.font.color.rgb = RGBColor(0, 0, 0)
                        elif clean_para.startswith("#### "):
                            # Xử lý Heading 4
                            text_clean = clean_para[5:].strip()
                            h4 = doc.add_heading(text_clean, level=4)
                            h4.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            for run in h4.runs:
                                _set_font(run, size=13, bold=True, italic=True)
                                run.font.color.rgb = RGBColor(0, 0, 0)
                        else:
                            _add_paragraph(doc, clean_para, style="Normal")
        
        doc.add_page_break()

    # 4. Global References
    refs = ket_qua.get("references", [])
    if refs:
        h1 = doc.add_heading("TÀI LIỆU THAM KHẢO", level=1)
        h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in h1.runs:
             _set_font(run, size=16, bold=True)
             run.font.color.rgb = RGBColor(0, 0, 0)
             
        # Sort by ID if possible
        try:
            refs = sorted(refs, key=lambda x: int(x.get("id", 0)) if isinstance(x, dict) else 0)
        except:
            pass

        for u in refs:
            p = doc.add_paragraph(style="Normal")
            p.paragraph_format.first_line_indent = Inches(0)  # APA hanging indent
            p.paragraph_format.left_indent = Inches(0.5)
            if isinstance(u, dict):
                # V37 APA Format: "1. Title. (Year, Date). In Wikipedia, The Free Encyclopedia. URL"
                ref_id = u.get('id', '')
                ref_title = u.get('title', 'Nguồn')
                ref_url = u.get('url', '')
                ref_year = u.get('year', 2026)
                ref_date = u.get('access_date', '')
                
                # Số thứ tự (bold)
                run_num = p.add_run(f"{ref_id}. ")
                _set_font(run_num, size=12, bold=True)
                
                # Title + năm
                date_str = f"{ref_year}, {ref_date}" if ref_date else str(ref_year)
                run_body = p.add_run(f"{ref_title}. ({date_str}). In ")
                _set_font(run_body, size=12)
                
                # Wikipedia italic
                run_wiki = p.add_run("Wikipedia, The Free Encyclopedia. ")
                _set_font(run_wiki, size=12, italic=True)
                
                # URL
                run_url = p.add_run(ref_url)
                _set_font(run_url, size=12)
            else:
                run = p.add_run(f"• {u}")
                _set_font(run, size=12)

    doc.save(duong_dan_docx)
