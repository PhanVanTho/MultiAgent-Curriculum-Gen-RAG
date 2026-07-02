# -*- coding: utf-8 -*-
import os
import re
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, PageTemplate, Frame, Flowable
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
    times_bi_path = "C:\\Windows\\Fonts\\timesbi.ttf"
    
    # Linux paths (example)
    if not os.path.exists(times_path):
         times_path = "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf"
         times_bd_path = "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf"
         times_it_path = "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Italic.ttf"
         times_bi_path = "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold_Italic.ttf"

    if os.path.exists(times_path) and os.path.exists(times_bd_path) and os.path.exists(times_it_path):
        pdfmetrics.registerFont(TTFont('Times-Roman', times_path))
        pdfmetrics.registerFont(TTFont('Times-Bold', times_bd_path))
        pdfmetrics.registerFont(TTFont('Times-Italic', times_it_path))
        
        has_bi = os.path.exists(times_bi_path)
        if has_bi:
            pdfmetrics.registerFont(TTFont('Times-BoldItalic', times_bi_path))
            
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily(
            'Times-Roman',
            normal='Times-Roman',
            bold='Times-Bold',
            italic='Times-Italic',
            boldItalic='Times-BoldItalic' if has_bi else 'Times-Bold'
        )
        FONT_NAME = 'Times-Roman'
        FONT_BOLD = 'Times-Bold'
        FONT_ITALIC = 'Times-Italic'
    else:
         # Fallback to Arial if Times not found
         arial_path = "C:\\Windows\\Fonts\\arial.ttf"
         arial_bd_path = "C:\\Windows\\Fonts\\arialbd.ttf"
         arial_it_path = "C:\\Windows\\Fonts\\ariali.ttf"
         arial_bi_path = "C:\\Windows\\Fonts\\arialbi.ttf"
         
         if not os.path.exists(arial_path):
              arial_path = "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"
              arial_bd_path = "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf"
              arial_it_path = "/usr/share/fonts/truetype/msttcorefonts/Arial_Italic.ttf"
              arial_bi_path = "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold_Italic.ttf"
         
         if os.path.exists(arial_path) and os.path.exists(arial_bd_path) and os.path.exists(arial_it_path):
              pdfmetrics.registerFont(TTFont('Arial', arial_path))
              pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bd_path))
              pdfmetrics.registerFont(TTFont('Arial-Italic', arial_it_path))
              
              has_abi = os.path.exists(arial_bi_path)
              if has_abi:
                   pdfmetrics.registerFont(TTFont('Arial-BoldItalic', arial_bi_path))
                   
              from reportlab.pdfbase.pdfmetrics import registerFontFamily
              registerFontFamily(
                  'Arial',
                  normal='Arial',
                  bold='Arial-Bold',
                  italic='Arial-Italic',
                  boldItalic='Arial-BoldItalic' if has_abi else 'Arial-Bold'
              )
              FONT_NAME = 'Arial'
              FONT_BOLD = 'Arial-Bold'
              FONT_ITALIC = 'Arial-Italic'
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

# Cover Page Title Style (centers within the 2.5cm border given leftMargin=3cm and rightMargin=2cm)
style_CoverTitle = ParagraphStyle(
    'CoverTitle',
    parent=style_Title,
    leftIndent=0.0,
    rightIndent=1.0*cm,
)

# Cover Page SubTitle Style
style_CoverSubTitle = ParagraphStyle(
    'CoverSubTitle',
    parent=style_Normal,
    fontName=FONT_NAME,
    fontSize=14,
    alignment=TA_CENTER,
    leftIndent=0.0,
    rightIndent=1.0*cm,
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

# TOC Styles
style_TOC_Chap = ParagraphStyle(
    'TOC_Chap',
    parent=styles['Normal'],
    fontName=FONT_BOLD,
    fontSize=11,
    leading=14,
    spaceBefore=4,
    spaceAfter=2
)
style_TOC_Sec = ParagraphStyle(
    'TOC_Sec',
    parent=styles['Normal'],
    fontName=FONT_NAME,
    fontSize=11,
    leading=14,
    leftIndent=0.3*inch,
    spaceAfter=2
)
style_TOC_Sub = ParagraphStyle(
    'TOC_Sub',
    parent=styles['Normal'],
    fontName=FONT_NAME,
    fontSize=11,
    leading=14,
    leftIndent=0.6*inch,
    spaceAfter=2
)
style_TOC_Page = ParagraphStyle(
    'TOC_Page',
    parent=styles['Normal'],
    fontName=FONT_NAME,
    fontSize=11,
    leading=14,
    alignment=TA_RIGHT
)

# (Hàm _clean_text cũ đã được thay thế bằng import từ bo_loc_html phía trên)

# --- 3. PAGE TEMPLATE (Header/Footer & Cover) ---
def cover_page(canvas, doc):
    canvas.saveState()
    # Khung viền đôi chuẩn đồ án/giáo trình
    canvas.setLineWidth(2)
    canvas.rect(2.5*cm, 2.5*cm, A4[0]-5*cm, A4[1]-5*cm)
    canvas.setLineWidth(0.5)
    canvas.rect(2.65*cm, 2.65*cm, A4[0]-5.3*cm, A4[1]-5.3*cm)
    canvas.restoreState()

def make_page_number_func(book_title):
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = "Trang %d" % page_num
        canvas.saveState()
        canvas.setFont(FONT_NAME, 10)
        # Footer Right
        canvas.drawRightString(A4[0] - 2.0*cm, 1.5 * cm, text)
        # Header Line
        canvas.setLineWidth(0.5)
        canvas.line(3.0*cm, A4[1]-1.5*cm, A4[0]-2.0*cm, A4[1]-1.5*cm)
        # Header Text
        canvas.setFont(FONT_ITALIC, 9)
        canvas.drawRightString(A4[0] - 2.0*cm, A4[1] - 1.3*cm, f"Giáo trình {book_title}")
        canvas.restoreState()
    return add_page_number

class PageRecorder(Flowable):
    def __init__(self, key, registry):
        super().__init__()
        self.key = key
        self.registry = registry

    def draw(self):
        if self.canv:
            self.registry[self.key] = self.canv.getPageNumber()

    def wrap(self, availWidth, availHeight):
        return 0, 0

def _xay_dung_story_pdf(ket_qua: dict, page_registry: dict | None = None) -> list:
    book = ket_qua.get("book_vi", {})
    story = []
    title = book.get("title", "GIÁO TRÌNH")

    # Helper to retrieve page number
    def get_page_str(key):
        if page_registry and key in page_registry:
            return str(page_registry[key])
        return ""

    # 1. TRANG BÌA
    story.append(Spacer(1, 3*inch))
    story.append(Paragraph(f"GIÁO TRÌNH<br/>{title.upper()}", style_CoverTitle))
    story.append(Spacer(1, 3*inch))
    story.append(Paragraph("Tác giả: Hệ thống AI Biên soạn tự động<br/>Năm xuất bản: 2026", style_CoverSubTitle))
    story.append(PageBreak())

    # 2. TABLE OF CONTENTS (Dynamic via page_registry)
    story.append(Paragraph("MỤC LỤC", style_Title))
    story.append(Spacer(1, 0.5*cm))
    
    chapters = book.get("chapters", [])
    
    # Using Table for cleaner TOC
    toc_data = []
    for idx, ch in enumerate(chapters, 1):
        # Chapter row
        ch_key = f"chap_{idx}"
        toc_data.append([
            Paragraph(f"CHƯƠNG {idx}: {ch.get('title','').upper()}", style_TOC_Chap),
            Paragraph(get_page_str(ch_key), style_TOC_Page)
        ])
        # Sections
        for jdx, sec in enumerate(ch.get("sections", []), 1):
            sec_key = f"sec_{idx}_{jdx}"
            toc_data.append([
                Paragraph(f"{idx}.{jdx}. {sec.get('title','')}", style_TOC_Sec),
                Paragraph(get_page_str(sec_key), style_TOC_Page)
            ])
            
            # Sub-sections (Level 3) in TOC
            content = sec.get("content", "")
            if content:
                sub_idx = 1
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("### "):
                        h3_title = line[4:].strip().replace('**', '').replace('`', '')
                        h3_title = re.sub(r'<[^>]+>', '', h3_title)
                        sub_key = f"sub_{idx}_{jdx}_{sub_idx}"
                        toc_data.append([
                            Paragraph(f"{idx}.{jdx}.{sub_idx}. {h3_title}", style_TOC_Sub),
                            Paragraph(get_page_str(sub_key), style_TOC_Page)
                        ])
                        sub_idx += 1
                    elif "Câu hỏi Ôn tập" in line or "Bài tập & Ôn tập" in line or "Review Questions" in line:
                        clean_line = line.replace('**', '').replace('###', '').strip()
                        if clean_line in ["Câu hỏi Ôn tập", "Bài tập & Ôn tập", "Review Questions"]:
                            rev_key = f"rev_{idx}_{jdx}"
                            toc_data.append([
                                Paragraph(clean_line, style_TOC_Sub),
                                Paragraph(get_page_str(rev_key), style_TOC_Page)
                            ])
    
    if toc_data:
        t = Table(toc_data, colWidths=[15*cm, 1*cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t)
    
    story.append(PageBreak())

    # 2.5 GLOSSARY (V33)
    glossary = ket_qua.get("glossary", [])
    if glossary:
        if page_registry is not None:
            story.append(PageRecorder("glossary", page_registry))
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
        if page_registry is not None:
            story.append(PageRecorder(f"chap_{idx}", page_registry))
        story.append(Paragraph(f"CHƯƠNG {idx}: {ch.get('title','').upper()}", style_H1))
        
        # Chapter Summary (Only for custom flow)
        if book.get("is_custom_flow"):
            summary = ch.get("summary", "")
            if summary:
                clean_sum = _clean_text(summary)
                story.append(Paragraph(f"<b>Tóm tắt chương:</b> {clean_sum}", style_Summary))
                story.append(Spacer(1, 0.3*cm))
        
        for jdx, sec in enumerate(ch.get("sections", []), 1):
            # Section Title
            if page_registry is not None:
                story.append(PageRecorder(f"sec_{idx}_{jdx}", page_registry))
            story.append(Paragraph(f"{idx}.{jdx}. {sec.get('title','')}", style_H2))
            
            # --- Lấy danh sách refs và map ID ---
            refs_list = ket_qua.get("references", [])
            ref_dict = {str(r.get("id")): r for r in refs_list if isinstance(r, dict)}
            
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
                        # Strip leading single/double digit list prefix like "1. ", "2. "
                        title_part = re.sub(r'^\d+\.\s*', '', title_part)
                        line = f"### {idx}.{jdx}.{sub_idx}. {title_part}"
                        sub_idx += 1
                    elif l_strip in ["**Câu hỏi Ôn tập**", "**Bài tập & Ôn tập**", "**Review Questions**"]:
                        line = f"### {l_strip.replace('**', '')}" # Make it H3 to be bold
                    
                    # Convert [ID] to APA Inline: (Title, Year)
                    def apa_replacer(match):
                        id_str = match.group(1)
                        ref = ref_dict.get(id_str)
                        if ref:
                            title_short = ref.get('title', 'Tài liệu')
                            if len(title_short) > 30: title_short = title_short[:30] + "..."
                            year = ref.get('year', 2026)
                            return f"({title_short}, {year})"
                        return match.group(0)
                    line = re.sub(r'\[(\d+)\]', apa_replacer, line)
                        
                    processed_lines.append(line)
                raw_content = '\n'.join(processed_lines)
            
            # CHUYỂN ĐỔI MARKDOWN SANG HTML TRƯỚC
            html_content = parse_markdown(raw_content)
            clean_content = _clean_text(html_content)
            
            # Replace existing newlines with <br/> so ReportLab maintains line breaks (especially in code blocks)
            clean_content = clean_content.replace('\n', '<br/>')
            
            # Split by the explicit block delimiter instead of newline
            paras = clean_content.split('|||BLOCK|||')
            
            sub_val = 1
            for p_text in paras:
                clean_p = p_text.strip()
                if not clean_p: continue
                
                # Dynamic page number tracking for sub-sections and review sections
                if page_registry is not None:
                    # Check for review headings
                    if clean_p in ["Câu hỏi Ôn tập", "Bài tập & Ôn tập", "Review Questions"] or clean_p.startswith("Câu hỏi Ôn tập") or clean_p.startswith("Bài tập & Ôn tập") or clean_p.startswith("Review Questions"):
                        story.append(PageRecorder(f"rev_{idx}_{jdx}", page_registry))
                    # Check for level-3 headings (e.g. "1.1.1. ...")
                    elif re.match(r'^\d+\.\d+\.\d+\.', clean_p):
                        story.append(PageRecorder(f"sub_{idx}_{jdx}_{sub_val}", page_registry))
                        sub_val += 1
                
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
    if page_registry is not None:
        story.append(PageRecorder("references", page_registry))
    story.append(Paragraph("TÀI LIỆU THAM KHẢO", style_H1))
    
    # APA Style for References (Hanging indent, no numbers)
    style_APA = ParagraphStyle(
        'APA',
        parent=style_Normal,
        firstLineIndent=-0.5*inch,
        leftIndent=0.5*inch,
        spaceAfter=8
    )
    
    refs = ket_qua.get("references", [])
    try:
        refs = sorted(refs, key=lambda x: str(x.get("title", "")).lower() if isinstance(x, dict) else str(x).lower())
    except:
        pass
        
    for u in refs:
         if isinstance(u, dict):
             # V37 APA Format: Title. (Year, Date). In Wikipedia, The Free Encyclopedia. URL
             ref_title = _clean_text(u.get('title', 'Nguồn'))
             ref_url = u.get('url', '')
             ref_year = u.get('year', 2026)
             ref_date = u.get('access_date', '')
             date_str = f"{ref_year}, {ref_date}" if ref_date else str(ref_year)
             ref_str = f"{ref_title}. ({date_str}). In <i>Wikipedia, The Free Encyclopedia</i>. <u>{ref_url}</u>"
             story.append(Paragraph(ref_str, style_APA))
         else:
             story.append(Paragraph(f"• {_clean_text(str(u))}", style_APA))
             
    return story

def xuat_pdf(ket_qua: dict, duong_dan_pdf: str):
    book = ket_qua.get("book_vi", {})
    title = book.get("title", "GIÁO TRÌNH")
    
    # Pass 1: Build to compile exact page numbers of all elements
    page_registry = {}
    doc1 = SimpleDocTemplate(
        duong_dan_pdf,
        pagesize=A4,
        rightMargin=2.0*cm,
        leftMargin=3.0*cm,
        topMargin=2.0*cm,
        bottomMargin=2.0*cm
    )
    story1 = _xay_dung_story_pdf(ket_qua, page_registry)
    add_page_number_func = make_page_number_func(title)
    doc1.build(story1, onFirstPage=cover_page, onLaterPages=add_page_number_func)
    
    # Pass 2: Re-generate the entire story using compiled registry and build final layout
    doc2 = SimpleDocTemplate(
        duong_dan_pdf,
        pagesize=A4,
        rightMargin=2.0*cm,
        leftMargin=3.0*cm,
        topMargin=2.0*cm,
        bottomMargin=2.0*cm
    )
    story2 = _xay_dung_story_pdf(ket_qua, page_registry)
    doc2.build(story2, onFirstPage=cover_page, onLaterPages=add_page_number_func)
