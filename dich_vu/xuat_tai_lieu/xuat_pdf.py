# -*- coding: utf-8 -*-
import os
import re
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, PageTemplate, Frame
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- IMPORT V21.5 ENTERPRISE CLEANER ---
from dich_vu.xuat_tai_lieu.bo_loc_html import clean_for_reportlab as _clean_text
from dich_vu.xuat_tai_lieu.markdown_parser import parse_markdown

logger = logging.getLogger(__name__)

# --- 1. FONTS SETUP ---
# Ưu tiên Times New Roman để chuẩn giáo trình
FONT_NAME = "Helvetica" # Fallback
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"

try:
    # Windows paths
    times_path = "C:\\Windows\\Fonts\\times.ttf"
    times_bd_path = "C:\\Windows\\Fonts\\timesbd.ttf"
    times_it_path = "C:\\Windows\\Fonts\\timesi.ttf"
    
    # Linux paths (example)
    if not os.path.exists(times_path):
         times_path = "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf"
         times_bd_path = "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf"
         times_it_path = "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Italic.ttf"

    if os.path.exists(times_path) and os.path.exists(times_bd_path) and os.path.exists(times_it_path):
        pdfmetrics.registerFont(TTFont('Times-Roman', times_path))
        pdfmetrics.registerFont(TTFont('Times-Bold', times_bd_path))
        pdfmetrics.registerFont(TTFont('Times-Italic', times_it_path))
        FONT_NAME = 'Times-Roman'
        FONT_BOLD = 'Times-Bold'
        FONT_ITALIC = 'Times-Italic'
    else:
         # Fallback to Arial if Times not found
         arial_path = "C:\\Windows\\Fonts\\arial.ttf"
         if os.path.exists(arial_path):
             pdfmetrics.registerFont(TTFont('Arial', arial_path))
             FONT_NAME = 'Arial'
             FONT_BOLD = 'Arial' # Simple fallback
             FONT_ITALIC = 'Arial'
except Exception as e:
    logger.warning(f"Font setup failed: {e}")

# --- 2. STYLES ---
styles = getSampleStyleSheet()

# Title Style
style_Title = ParagraphStyle(
    'CustomTitle',
    parent=styles['Title'],
    fontName=FONT_BOLD,
    fontSize=24,
    leading=30,
    alignment=TA_CENTER,
    spaceAfter=20,
    textColor=colors.black
)

# Chapter Heading (Heading 1)
style_H1 = ParagraphStyle(
    'CustomH1',
    parent=styles['Heading1'],
    fontName=FONT_BOLD,
    fontSize=16,
    leading=20,
    alignment=TA_CENTER,
    spaceAfter=12,
    textColor=colors.black # Màu đen chuẩn
)

# Section Heading (Heading 2)
style_H2 = ParagraphStyle(
    'CustomH2',
    parent=styles['Heading2'],
    fontName=FONT_BOLD,
    fontSize=14,
    leading=18,
    alignment=TA_LEFT,
    spaceBefore=12,
    spaceAfter=6,
    textColor=colors.black
)

# Normal Text (Justified, Indented)
style_Normal = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontName=FONT_NAME,
    fontSize=12,
    leading=15, # Line spacing 1.3 approx
    alignment=TA_JUSTIFY, # Căn đều 2 bên
    firstLineIndent=0.5 * inch, # Thụt đầu dòng
    spaceAfter=6
)

# List Items
style_List = ParagraphStyle(
    'CustomList',
    parent=styles['Normal'],
    fontName=FONT_NAME,
    fontSize=12,
    leading=15,
    alignment=TA_LEFT,
    leftIndent=0.5 * inch,
    spaceAfter=2
)

# Citation/Italic
style_Italic = ParagraphStyle(
    'CustomItalic',
    parent=styles['Normal'],
    fontName=FONT_ITALIC,
    fontSize=10,
    leading=12,
    alignment=TA_LEFT,
    textColor=colors.grey,
    spaceAfter=6
)

# V33: Chapter Summary
style_Summary = ParagraphStyle(
    'ChapterSummary',
    parent=styles['Normal'],
    fontName=FONT_ITALIC,
    fontSize=11,
    leading=14,
    alignment=TA_JUSTIFY,
    leftIndent=0.4 * inch,
    rightIndent=0.4 * inch,
    spaceBefore=6,
    spaceAfter=12,
    textColor=colors.HexColor('#333333'),
    borderPadding=6,
)

# V33: Glossary Term
style_GlossaryTerm = ParagraphStyle(
    'GlossaryTerm',
    parent=styles['Normal'],
    fontName=FONT_NAME,
    fontSize=12,
    leading=15,
    alignment=TA_LEFT,
    spaceAfter=4
)

# (Hàm _clean_text cũ đã được thay thế bằng import từ bo_loc_html phía trên)

# --- 3. PAGE TEMPLATE (Header/Footer) ---
def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = "Trang %d" % page_num
    canvas.saveState()
    canvas.setFont(FONT_NAME, 9)
    # Footer Center
    canvas.drawCentredString(A4[0] / 2.0, 1.5 * cm, text)
    # Header Line
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, A4[1]-2*cm, A4[0]-2*cm, A4[1]-2*cm)
    canvas.restoreState()

def xuat_pdf(ket_qua: dict, duong_dan_pdf: str):
    book = ket_qua.get("book_vi", {})
    doc = SimpleDocTemplate(
        duong_dan_pdf,
        pagesize=A4,
        rightMargin=2.0*cm,
        leftMargin=3.0*cm, # Lề trái 3cm chuẩn đóng gáy BGDĐT
        topMargin=2.0*cm,
        bottomMargin=2.0*cm
    )
    
    story = []

    # 1. TITLE PAGE
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph(book.get("title", "GIÁO TRÌNH").upper(), style_Title))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Tài liệu biên soạn tự động bởi hệ thống AI", 
                           ParagraphStyle('SubTitle', parent=style_Normal, alignment=TA_CENTER, fontName=FONT_ITALIC)))
    story.append(PageBreak())

    # 2. TABLE OF CONTENTS (Static)
    story.append(Paragraph("MỤC LỤC", style_Title))
    story.append(Spacer(1, 0.5*cm))
    
    chapters = book.get("chapters", [])
    
    # Using Table for cleaner TOC
    toc_data = []
    for idx, ch in enumerate(chapters, 1):
        # Chapter row
        toc_data.append([f"CHƯƠNG {idx}: {ch.get('title','').upper()}", ""])
        # Sections
        for jdx, sec in enumerate(ch.get("sections", []), 1):
            toc_data.append([f"   {idx}.{jdx}. {sec.get('title','')}", ""]) # Indent visualization
            
            # Sub-sections (Level 3) in TOC
            content = sec.get("content", "")
            if content:
                sub_idx = 1
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("### "):
                        h3_title = line[4:].strip().replace('**', '').replace('`', '')
                        h3_title = re.sub(r'<[^>]+>', '', h3_title)
                        toc_data.append([f"      {idx}.{jdx}.{sub_idx}. {h3_title}", ""])
                        sub_idx += 1
                    elif "Câu hỏi Ôn tập" in line or "Bài tập & Ôn tập" in line:
                        clean_line = line.replace('**', '').replace('###', '').strip()
                        if clean_line in ["Câu hỏi Ôn tập", "Bài tập & Ôn tập"]:
                            toc_data.append([f"      {clean_line}", ""])
    
    if toc_data:
        t = Table(toc_data, colWidths=[15*cm, 1*cm])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t)
    
    story.append(PageBreak())

    # 2.5 GLOSSARY (V33)
    glossary = ket_qua.get("glossary", [])
    if glossary:
        story.append(Paragraph("BẢNG THUẬT NGỮ", style_H1))
        story.append(Spacer(1, 0.3*cm))
        for item in glossary:
            term = _clean_text(item.get('term', ''))
            definition = _clean_text(item.get('definition', ''))
            story.append(Paragraph(f"<b>{term}</b>: {definition}", style_GlossaryTerm))
        story.append(PageBreak())

    # 3. CONTENT
    for idx, ch in enumerate(chapters, 1):
        # Chapter Title
        story.append(Paragraph(f"CHƯƠNG {idx}: {ch.get('title','').upper()}", style_H1))
        
        # V33: Chapter Summary (Đã ẩn theo yêu cầu)
        # summary = ch.get("summary", "")
        # if summary:
        #     clean_summary = _clean_text(summary)
        #     story.append(Paragraph(f"<i>Tóm tắt chương: {clean_summary}</i>", style_Summary))

        
        for jdx, sec in enumerate(ch.get("sections", []), 1):
            # Section Title
            story.append(Paragraph(f"{idx}.{jdx}. {sec.get('title','')}", style_H2))
            
            # Content separation
            raw_content = sec.get("content", "")
            
            # --- NUMBERING LEVEL 3 HEADINGS ---
            if raw_content:
                sub_idx = 1
                processed_lines = []
                for line in raw_content.split('\n'):
                    l_strip = line.strip()
                    if l_strip.startswith("### "):
                        title_part = l_strip[4:].strip()
                        line = f"### {idx}.{jdx}.{sub_idx}. {title_part}"
                        sub_idx += 1
                    elif l_strip in ["**Câu hỏi Ôn tập**", "**Bài tập & Ôn tập**"]:
                        line = f"### {l_strip.replace('**', '')}" # Make it H3 to be bold
                    processed_lines.append(line)
                raw_content = '\n'.join(processed_lines)
            
            # CHUYỂN ĐỔI MARKDOWN SANG HTML TRƯỚC
            html_content = parse_markdown(raw_content)
            
            clean_content = _clean_text(html_content)
            
            # Replace existing newlines with <br/> so ReportLab maintains line breaks (especially in code blocks)
            clean_content = clean_content.replace('\n', '<br/>')
            
            # Split by the explicit block delimiter instead of newline
            paras = clean_content.split('|||BLOCK|||')
            
            for p_text in paras:
                clean_p = p_text.strip()
                if not clean_p: continue
                
                # ReportLab list items fallback (nếu parse_markdown tạo ra text bắt đầu bằng bullet)
                if clean_p.startswith("- ") or clean_p.startswith("* ") or clean_p.startswith("• "):
                    clean_p = clean_p[2:].strip()
                    story.append(Paragraph(f"• {clean_p}", style_List))
                elif re.match(r'^\d+\.\s', clean_p):
                    story.append(Paragraph(clean_p, style_List))
                elif clean_p == "---":
                    # Xử lý đường kẻ ngang
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Table([[""]], colWidths=[15*cm], style=TableStyle([('LINEABOVE', (0,0), (-1,-1), 1, colors.grey)])))
                    story.append(Spacer(1, 0.1*inch))
                else:
                    story.append(Paragraph(clean_p, style_Normal))

        story.append(PageBreak())

    # 4. REFERENCES
    story.append(Paragraph("TÀI LIỆU THAM KHẢO", style_H1))
    refs = ket_qua.get("references", [])
    try:
        refs = sorted(refs, key=lambda x: int(x.get("id", 0)) if isinstance(x, dict) else 0)
    except:
        pass
        
    for u in refs:
         if isinstance(u, dict):
             # V37 APA Format
             ref_id = u.get('id', '')
             ref_title = _clean_text(u.get('title', 'Nguồn'))
             ref_url = u.get('url', '')
             ref_year = u.get('year', 2026)
             ref_date = u.get('access_date', '')
             date_str = f"{ref_year}, {ref_date}" if ref_date else str(ref_year)
             ref_str = f"<b>{ref_id}.</b> {ref_title}. ({date_str}). In <i>Wikipedia, The Free Encyclopedia</i>. <u>{ref_url}</u>"
             story.append(Paragraph(ref_str, style_Normal))
         else:
             story.append(Paragraph(f"• {u}", style_List))

    # Build PDF
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
