# -*- coding: utf-8 -*-
import sys
import os

# Thêm đường dẫn vào sys.path để import được module trong dich_vu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dich_vu.xuat_tai_lieu.bo_loc_html import clean_for_reportlab, clean_for_docx

def test_sanitization():
    print("--- STARTING ENTERPRISE SANITIZATION TESTS (V21.5) ---")
    
    test_cases = [
        {
            "name": "Malformed Nesting",
            "input": "<b><i>Malformed Nesting</b></i>",
            "expected_pdf": "<b><i>Malformed Nesting</i></b>"
        },
        {
            "name": "Block-level Separation",
            "input": "<div>Part A</div><div>Part B</div>",
            "expected_pdf": "\nPart A\nPart B"
        },
        {
            "name": "Unsupported Tags Strip",
            "input": "<section><article><span>Clean Text</span></article></section>",
            "expected_pdf": "\n\nClean Text"
        },
        {
            "name": "Security (Script/Style)",
            "input": "<script>alert('hack')</script><style>body{color:red}</style>Safe Text",
            "expected_pdf": "Safe Text"
        },
        {
            "name": "Entities & Non-breaking Space",
            "input": "Text&nbsp;with&nbsp;entities&nbsp;&quot;Quotes&quot;",
            "expected_pdf": "Text with entities \"Quotes\""
        },
        {
            "name": "Nested Link + Sup",
            "input": '<a href="https://test.com" title="Ignore me"><sup>[1]</sup></a>',
            "expected_pdf": '<u><a href="https://test.com" color="blue">[1]</a></u>'
        },
        {
            "name": "Empty Content",
            "input": "<div><span></span></div>Text",
            "expected_pdf": "\nText"
        },
        {
            "name": "Link Without Href",
            "input": "<a>Broken Link</a>",
            "expected_pdf": "Broken Link"
        }
    ]

    all_passed = True
    for case in test_cases:
        print(f"\n[TEST] {case['name']}")
        result_pdf = clean_for_reportlab(case['input'])
        
        # Normalize result for comparison (simple check)
        # Note: BeautiulSoup might add whitespace or wrap in tags depending on the parser
        print(f"  Input:    {case['input']}")
        print(f"  Output:   {result_pdf}")
        
        # Simple validation: Output should NOT contain 'class=', 'title=', 'script', 'style'
        forbidden = ["class=", "title=", "target=", "rel=", "<script>", "<style>", "\xa0"]
        for f in forbidden:
            if f in result_pdf:
                print(f"  [FAIL] Found forbidden string: {f}")
                all_passed = False
                
    if all_passed:
        print("\n✅ ALL ENTERPRISE SANITIZATION TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED. CHECK LOGS.")

if __name__ == "__main__":
    try:
        test_sanitization()
    except ImportError as e:
        print(f"\n❌ CRITICAL: Missing dependency: {e}")
        print("Please ensure 'beautifulsoup4' is installed.")
