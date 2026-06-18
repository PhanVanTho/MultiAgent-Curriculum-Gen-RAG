# -*- coding: utf-8 -*-
import os
import unittest
import sys
import json
import re
from unittest.mock import patch, MagicMock

# Patch environment and load_dotenv BEFORE importing ung_dung
import dotenv
orig_load_dotenv = dotenv.load_dotenv
def mock_load_dotenv(*args, **kwargs):
    res = orig_load_dotenv(*args, **kwargs)
    os.environ["DB_USE_SQLITE"] = "True"
    return res
dotenv.load_dotenv = mock_load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ung_dung import is_valid_query, is_gibberish, is_meaningful, is_abbreviation
from dich_vu.safety_router import (
    classify_topic, rule_based_filter, get_block_message, reframe_topic, generate_safe_title
)
from dich_vu.gap_filler import identify_knowledge_gaps
from dich_vu.audit_service import ScholarlyAuditEngine

class TestPipelineAndRAG(unittest.TestCase):
    def tearDown(self):
        from ung_dung import app
        from mo_hinh import db
        with app.app_context():
            db.session.remove()
        import threading
        for t in threading.enumerate():
            if t.name == "pipeline_thread" and t.is_alive():
                t.join(timeout=2.0)

    def test_input_validation(self):
        # is_valid_query
        self.assertTrue(is_valid_query("Vật lý hạt nhân"))
        self.assertTrue(is_valid_query("AI và Robotics"))
        self.assertFalse(is_valid_query("chế bom!!!")) # Special characters
        
        # is_gibberish
        self.assertTrue(is_gibberish("asdfghjklqwerty"))
        self.assertFalse(is_gibberish("Trí tuệ nhân tạo"))
        
        # is_meaningful
        self.assertTrue(is_meaningful("Học máy"))
        self.assertFalse(is_meaningful("a"))
        self.assertFalse(is_meaningful("zxcvbn"))

        # is_abbreviation
        self.assertTrue(is_abbreviation("NSND"))
        self.assertFalse(is_abbreviation("CNTT")) # Allowed common abbreviation
        self.assertFalse(is_abbreviation("AI"))  # Allowed common abbreviation
        self.assertFalse(is_abbreviation("Vật lý học"))

    def test_safety_router_rule_based(self):
        # 1. Hard Block
        res = rule_based_filter("Cách chế tạo bom xăng")
        self.assertEqual(res["classification"], "BLOCK")
        self.assertEqual(res["block_type"], "hard")
        
        # 2. Soft Block (Sensitive)
        res_soft = rule_based_filter("Lịch sử vũ khí hạt nhân")
        self.assertEqual(res_soft["classification"], "REFRAME")
        self.assertEqual(res_soft["block_type"], "soft")
        
        # 3. Safe
        res_safe = rule_based_filter("Toán học cao cấp")
        self.assertEqual(res_safe["classification"], "SAFE")

    @patch("dich_vu.safety_router._ai_classify")
    def test_safety_router_classify(self, mock_ai):
        # Case 1: Safe topic
        mock_ai.return_value = {"classification": "SAFE", "reason": "Approved by AI", "layer": "ai"}
        res = classify_topic("Cơ học lượng tử", "mock-key")
        self.assertEqual(res["classification"], "SAFE")
        
        # Case 2: Hard Block keyword should bypass AI check entirely
        res_hard = classify_topic("chế tạo bom", "mock-key")
        self.assertEqual(res_hard["classification"], "BLOCK")
        self.assertEqual(res_hard["layer"], "rule")
        
        # Case 3: Academic Override: AI says BLOCK but topic is clearly academic without action verbs
        mock_ai.return_value = {"classification": "BLOCK", "reason": "Sensitive keyword detected", "layer": "ai"}
        res_override = classify_topic("Nguyên lý hoạt động của lò phản ứng hạt nhân", "mock-key")
        self.assertEqual(res_override["classification"], "REFRAME")
        self.assertEqual(res_override["layer"], "academic_override")

    def test_safety_block_ux_messages(self):
        # Hard block message
        hard_res = {"classification": "BLOCK", "block_type": "hard", "layer": "rule"}
        msg = get_block_message(hard_res)
        self.assertIn("Nội dung không được phép", msg["title"])
        
        # Soft block message
        soft_res = {"classification": "REFRAME", "block_type": "soft", "layer": "rule"}
        msg_soft = get_block_message(soft_res)
        self.assertIn("Chủ đề nhạy cảm", msg_soft["title"])
        
        # Safe should return None
        safe_res = {"classification": "SAFE"}
        self.assertIsNone(get_block_message(safe_res))

    @patch("dich_vu.gap_filler.tim_kiem_vector")
    def test_gap_filling_detection(self, mock_vector_search):
        # Setup mock outline
        outline = [
            {
                "title": "Chương 1: Giới thiệu",
                "sections": [
                    {"title": "1.1 Khái niệm cơ bản"},
                    {"title": "1.2 Lịch sử phát triển"}
                ]
            }
        ]
        
        # Mock vector search scores:
        # First query (1.1) returns a high score (0.80) -> Safe
        # Second query (1.2) returns a low score (0.45) -> Gap
        mock_vector_search.side_effect = [
            [{"score": 0.80}],
            [{"score": 0.45}]
        ]
        
        gaps = identify_knowledge_gaps(outline, [{"id": "doc1", "content": "text"}], "mock-key", "Trí tuệ nhân tạo")
        
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["chapter"], "Chương 1: Giới thiệu")
        self.assertEqual(gaps[0]["section"], "1.2 Lịch sử phát triển")
        self.assertTrue(gaps[0]["score"] < 0.54)

    @patch("dich_vu.embedding_pool.embedding_pool")
    @patch("google.genai.Client")
    def test_scholarly_audit_engine(self, mock_genai, mock_pool):
        # Mock embeddings
        mock_pool.embed_content.return_value = [
            [0.95, 0.05, 0.0], # Claim 1
            [0.1, 0.8, 0.1], # Claim 2
            [0.9, 0.1, 0.0], # Span 1 (High similarity)
            [0.9, 0.1, 0.0], # Span 2 (Low similarity)
        ]
        
        engine = ScholarlyAuditEngine("mock-openai-key", ["mock-gemini-key"])
        
        fact_mappings = [
            {"claim": "AI can learn.", "span": "AI is capable of learning.", "source_id": "1"},
            {"claim": "AI is a vegetable.", "span": "AI is a computer system.", "source_id": "2"}
        ]
        
        scored = engine.calculate_vector_scores(fact_mappings)
        self.assertEqual(len(scored), 2)
        
        # Verify first has high vector score, second has lower
        self.assertTrue(scored[0]["vector_score"] > 0.90)
        self.assertTrue(scored[1]["vector_score"] < 0.30)
        
        # Run full audit
        # Mock V8.1 alignment passes (since mappings has source_id "1" and "2" matching citation IDs in content)
        section_data = {
            "content": "AI is smart [1] and very advanced [2].",
            "fact_mappings": scored
        }
        
        # Mock Gemini Soft-Audit response for the low similarity claim (which NLI will filter as CONTRADICTION or UNCERTAIN)
        mock_client_instance = mock_genai.return_value
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "audit_results": [
                {
                    "claim_index": 1,
                    "verdict": "NO",
                    "error_type": "contradiction",
                    "confidence": 0.95,
                    "reason": "Claim states AI is a vegetable, which contradicts Span."
                }
            ]
        })
        mock_client_instance.models.generate_content.return_value = mock_response
        
        audit_res = engine.run_full_audit(section_data, "Trí tuệ nhân tạo")
        self.assertEqual(audit_res["status"], "fail")
        self.assertEqual(audit_res["error_count"], 1)
        self.assertEqual(audit_res["has_critical_contradiction"], True)

    def test_grounding_score_calculation(self):
        # Simulate final chapters structure
        final_chapters = [
            {
                "title": "Chương 1: Tổng quan",
                "sections": [
                    {
                        "content": "Paragraph one is short but has a citation <span class=\"citation-apa\">[1]</span>.\n"
                                   "Paragraph two is very long and has no citation but is fine.\n"
                                   "### Heading section to ignore\n"
                                   "1. Numbered question to ignore\n"
                                   "### Câu hỏi Ôn tập\n"
                                   "Paragraph three in review section that should be ignored entirely."
                    }
                ]
            }
        ]
        
        # We recreate the Grounding Score logic here to verify its mathematical correctness
        grounding_stats = {"chapters": [], "overall": {}}
        total_paras_all = 0
        grounded_paras_all = 0

        for chap in final_chapters:
            chap_title_gs = chap.get("title", "")
            chap_total = 0
            chap_grounded = 0
            for sec in chap.get("sections", []):
                content_gs = sec.get("content", "")
                
                review_pattern = re.compile(
                    r'(###\s*)?\*{0,2}(Câu hỏi Ôn tập|Bài tập\s*[&＆]\s*Ôn tập|Review Questions)\*{0,2}',
                    re.IGNORECASE
                )
                for line in content_gs.split("\n"):
                    if review_pattern.search(line.strip()):
                        content_gs = content_gs.split(line)[0]
                        break

                paragraphs = [
                    p.strip() for p in content_gs.split("\n")
                    if p.strip()
                    and not p.strip().startswith("### ")
                    and not re.match(r'^\d+\.\s', p.strip())
                    and len(p.strip()) >= 40
                ]
                
                for para in paragraphs:
                    chap_total += 1
                    if re.search(r'<span class="citation-apa">', para) or re.search(r'<sup class="citation">', para) or re.search(r'\[\d+\]', para):
                        chap_grounded += 1
                        
            ratio_gs = (chap_grounded / chap_total * 100) if chap_total > 0 else 0
            grounding_stats["chapters"].append({
                "title": chap_title_gs, "total": chap_total,
                "grounded": chap_grounded, "ratio": round(ratio_gs, 1)
            })
            total_paras_all += chap_total
            grounded_paras_all += chap_grounded

        overall_ratio = (grounded_paras_all / total_paras_all * 100) if total_paras_all > 0 else 0
        
        # Verify:
        # Paragraph 1: "Paragraph one is short but has a citation <span class="citation-apa">[1]</span>." (len = 70 >= 40, contains citation-apa -> Grounded)
        # Paragraph 2: "Paragraph two is very long and has no citation but is fine." (len = 59 >= 40, no citation -> Ungrounded)
        # Heading & question are excluded. Review section paragraph is excluded.
        # Total = 2, Grounded = 1. Ratio = 50%.
        self.assertEqual(total_paras_all, 2)
        self.assertEqual(grounded_paras_all, 1)
        self.assertEqual(overall_ratio, 50.0)

    def test_scale_audit_warning_rendering(self):
        from ung_dung import app, CONG_VIEC
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        
        # Mock a job in CONG_VIEC
        ma_cv = "test_scale_job"
        CONG_VIEC[ma_cv] = {
            "trang_thai": "hoan_thanh",
            "tieu_de": "Test Scale Warning",
            "tai_docx": "/tai/docx/test",
            "tai_pdf": "/tai/pdf/test",
            "tai_docx_plain": "/tai/docx/test_plain",
            "tai_pdf_plain": "/tai/pdf/test_plain",
            "nguon": [],
            "audit_quy_mo": {
                "status": "fail",
                "scores": {"coverage": 0.60, "density": 0.55, "length": 0.50},
                "stats": {
                    "actual_chapters": 5,
                    "required_chapters_min": 7,
                    "estimated_pages": 15.0,
                    "required_pages_min": 30
                },
                "missing_topics": ["Quantum gravity", "Black hole entropy"]
            }
        }
        
        # Also mock the JSON file so the route doesn't crash trying to load it
        import shutil
        from cau_hinh import CauHinh
        p_json = os.path.join(CauHinh.THU_MUC_JSON, f"{ma_cv}.json")
        os.makedirs(CauHinh.THU_MUC_JSON, exist_ok=True)
        with open(p_json, "w", encoding="utf-8") as f:
            json.dump({
                "book_vi": {"title": "Test Scale Warning", "chapters": []},
                "references": [],
                "audit_quy_mo": CONG_VIEC[ma_cv]["audit_quy_mo"]
            }, f)
            
        try:
            mock_user = MagicMock()
            mock_user.is_authenticated = True
            mock_user.ho_ten = "Test User"
            mock_user.ten_dang_nhap = "testuser"
            mock_user.anh_dai_dien = None
            mock_user.token = 100
            
            with patch("flask_login.utils._get_user", return_value=mock_user):
                resp = client.get(f"/ket_qua/{ma_cv}")
            self.assertEqual(resp.status_code, 200)
            html = resp.data.decode("utf-8")
            
            # Verify warning elements are present
            self.assertIn("result.scale_warning_title", html)
            self.assertIn("60%", html) # coverage
            self.assertIn("55%", html) # density
            self.assertIn("50%", html) # length
            self.assertIn("Quantum gravity", html)
            self.assertIn("Black hole entropy", html)
        finally:
            if os.path.exists(p_json):
                os.remove(p_json)

    @patch("dich_vu.lay_wikipedia.ekre_discovery_engine")
    @patch("sys.exit", side_effect=SystemExit)
    @patch("builtins.print")
    def test_cli_pipeline_insufficient_data(self, mock_print, mock_exit, mock_ekre):
        from cli import run_cli_pipeline
        # Mock ekre_discovery_engine to return no reliable docs
        mock_ekre.return_value = {
            "passages": [],
            "candidates": {},
            "hardened_docs": [],
            "xray": {"stats": {"confidence_score": 0.0}}
        }
        
        # Run pipeline
        try:
            run_cli_pipeline("asdfghjklqwe123", "tieu_chuan", "vi", "./output_test")
        except SystemExit:
            pass
            
        # Verify it printed the standardized message
        printed_messages = [call[0][0] for call in mock_print.call_args_list if len(call[0]) > 0]
        matched = any("Thông tin tìm kiếm của bạn trên Wikipedia không đủ để viết một bài giáo trình." in msg for msg in printed_messages)
        self.assertTrue(matched)
        mock_exit.assert_called_with(1)

    def test_xac_nhan_ha_quy_mo_endpoint(self):
        from ung_dung import app, CONG_VIEC
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        
        ma_cv = "test_confirm_job"
        CONG_VIEC[ma_cv] = {
            "trang_thai": "cho_xac_nhan",
            "xac_nhan_cho_phep": None
        }
        
        # Test dong_y
        resp = client.post(f"/xac_nhan/{ma_cv}/dong_y")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CONG_VIEC[ma_cv]["xac_nhan_cho_phep"], True)
        
        # Test tu_choi
        CONG_VIEC[ma_cv]["xac_nhan_cho_phep"] = None
        resp = client.post(f"/xac_nhan/{ma_cv}/tu_choi")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CONG_VIEC[ma_cv]["xac_nhan_cho_phep"], False)
        
        # Clean up
        del CONG_VIEC[ma_cv]

    def test_xac_nhan_ha_so_chuong_endpoint(self):
        from ung_dung import app, CONG_VIEC
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        
        ma_cv = "test_confirm_chapters_job"
        CONG_VIEC[ma_cv] = {
            "trang_thai": "cho_xac_nhan",
            "loai_loi": "CUSTOM_CHAPTER_DOWNGRADE",
            "xac_nhan_cho_phep": None
        }
        
        # Test dong_y
        resp = client.post(f"/xac_nhan/{ma_cv}/dong_y")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CONG_VIEC[ma_cv]["xac_nhan_cho_phep"], True)
        
        # Test tu_choi
        CONG_VIEC[ma_cv]["xac_nhan_cho_phep"] = None
        resp = client.post(f"/xac_nhan/{ma_cv}/tu_choi")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CONG_VIEC[ma_cv]["xac_nhan_cho_phep"], False)
        
        # Clean up
        del CONG_VIEC[ma_cv]

    def test_dich_tai_lieu_en_sang_vi(self):
        from unittest.mock import MagicMock, patch
        from dich_vu.lay_wikipedia import dich_tai_lieu_en_sang_vi
        
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="Bản dịch tiếng Việt"))]
        mock_client.chat.completions.create.return_value = mock_resp
        
        with patch("openai.OpenAI", return_value=mock_client):
            res = dich_tai_lieu_en_sang_vi("English text", "dummy_key")
            self.assertEqual(res, "Bản dịch tiếng Việt")

    @patch("dich_vu.safety_router.OpenAI")
    @patch("openai.OpenAI")
    @patch("threading.Thread")
    def test_semantic_outline_validation_blocked(self, mock_thread, mock_openai, mock_safety_openai):
        from unittest.mock import MagicMock, patch
        from ung_dung import app, CONG_VIEC
        
        class SyncThread:
            def __init__(self, *args, **kwargs):
                self.target = kwargs.get("target")
                self.args = kwargs.get("args", ())
                self.kwargs = kwargs.get("kwargs", {})
            def start(self):
                if self.target:
                    self.target(*self.args, **self.kwargs)
                
        class SyncExecutor:
            def __init__(self, *args, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            def submit(self, fn, *args, **kwargs):
                future = MagicMock()
                try:
                    res = fn(*args, **kwargs)
                    future.result.return_value = res
                except Exception as e:
                    future.result.side_effect = e
                return future
                
        mock_thread.side_effect = SyncThread
        
        mock_client = MagicMock()
        
        def mock_create(*args, **kwargs):
            messages = kwargs.get("messages", [])
            content = messages[0]["content"] if messages else ""
            mock_res = MagicMock()
            if "Kiểm tra từng tên chương" in content or "Danh sách tên chương" in content:
                mock_res.choices = [MagicMock(message=MagicMock(content="[false, false, true]"))]
            else:
                mock_res.choices = [MagicMock(message=MagicMock(content='{"classification": "SAFE", "reason": "Safe topic"}'))]
            return mock_res
            
        mock_client.chat.completions.create.side_effect = mock_create
        
        mock_openai.return_value = mock_client
        mock_safety_openai.return_value = mock_client
        
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        
        with patch("concurrent.futures.ThreadPoolExecutor", SyncExecutor):
            resp = client.post("/tao", json={
                "tieu_de": "Trí tuệ nhân tạo",
                "so_chuong_custom": 3,
                "danh_sach_chuong": ["Sinh học là gì", "sadsa", "Trí tuệ nhân tạo là gì"]
            })
            self.assertEqual(resp.status_code, 200)
            ma_cv = resp.get_json()["ma_cv"]
            
            self.assertEqual(CONG_VIEC[ma_cv]["trang_thai"], "that_bai")
            self.assertEqual(CONG_VIEC[ma_cv]["loai_loi"], "semantic_drift")
            self.assertIn("Sinh học là gì", CONG_VIEC[ma_cv]["loi"])
            self.assertIn("sadsa", CONG_VIEC[ma_cv]["loi"])
        
        # Clean up
        del CONG_VIEC[ma_cv]

    def test_custom_chapters_validation(self):
        from ung_dung import app
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        
        # Test case 1: Title contains abbreviation
        resp = client.post("/tao", json={
            "tieu_de": "NSND",
            "so_chuong_custom": 1
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Chủ đề chứa từ viết tắt", resp.get_json()["loi"])
        
        # Test case 2: Custom chapter contains abbreviation
        resp = client.post("/tao", json={
            "tieu_de": "Trí tuệ nhân tạo",
            "so_chuong_custom": 2,
            "danh_sach_chuong": ["Trí tuệ nhân tạo là gì", "NSND ứng dụng"]
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("chứa từ viết tắt", resp.get_json()["loi"])
        
        # Test case 3: Custom chapter exceeds 100 characters
        long_chapter = "A" * 101
        resp = client.post("/tao", json={
            "tieu_de": "Trí tuệ nhân tạo",
            "so_chuong_custom": 2,
            "danh_sach_chuong": ["Trí tuệ nhân tạo là gì", long_chapter]
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vượt quá giới hạn 100 ký tự", resp.get_json()["loi"])

        # Test case 4: Custom chapter contains empty string
        resp = client.post("/tao", json={
            "tieu_de": "Trí tuệ nhân tạo",
            "so_chuong_custom": 2,
            "danh_sach_chuong": ["Trí tuệ nhân tạo là gì", "  "]
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("không được để trống", resp.get_json()["loi"])

    def test_giam_sat_quy_mo_custom_chapters(self):
        from dich_vu.gemini_giam_sat import giam_sat_quy_mo
        # Giả lập sách có 3 chương, mỗi chương có các section
        mock_chapters = [
            {
                "title": f"Chương {i}",
                "sections": [
                    {"title": f"Mục {i}.1", "content": "Nội dung mục 1 " * 100}, # 1500 ký tự
                    {"title": f"Mục {i}.2", "content": "Nội dung mục 2 " * 100},
                ]
            }
            for i in range(1, 4) # 3 chương
        ]
        
        # Test 1: Quy mô "tieu_chuan" (mặc định cần 7 chương). Nếu không truyền so_chuong_yeu_cau, nó sẽ fail.
        # Sử dụng api_keys rỗng để test phần local check trước.
        res_fail = giam_sat_quy_mo(
            chu_de="Tây Du Ký",
            final_chapters=mock_chapters,
            quy_mo="tieu_chuan",
            api_keys=["mock_key"], # Cần key khác rỗng để không bị bypass pass
            so_chuong_yeu_cau=0
        )
        self.assertEqual(res_fail["status"], "fail")
        self.assertTrue(any("Thiếu chương" in issue for issue in res_fail["issues"]))

        # Test 2: Có truyền so_chuong_yeu_cau=3. Số chương min sẽ được đặt thành 3.
        # Số trang min mới: 30 * 3 / 7 = 13 trang.
        # Tổng ký tự thực tế: 3 chương * 2 mục * 1500 ký tự = 9000 ký tự.
        # Estimated pages = 9000 / 1800 = 5.0 trang.
        # Vì 5.0 trang < 13 trang, nó vẫn fail do thiếu nội dung (không fail do thiếu chương).
        res_fail_page = giam_sat_quy_mo(
            chu_de="Tây Du Ký",
            final_chapters=mock_chapters,
            quy_mo="tieu_chuan",
            api_keys=["mock_key"],
            so_chuong_yeu_cau=3
        )
        self.assertEqual(res_fail_page["status"], "fail")
        self.assertFalse(any("Thiếu chương" in issue for issue in res_fail_page["issues"]))
        self.assertTrue(any("Thiếu nội dung" in issue for issue in res_fail_page["issues"]))

        # Test 3: Sách đủ cả chương và trang
        mock_chapters_heavy = [
            {
                "title": f"Chương {i}",
                "sections": [
                    {"title": f"Mục {i}.1", "content": "Nội dung mục 1 " * 400}, # 6000 ký tự
                    {"title": f"Mục {i}.2", "content": "Nội dung mục 2 " * 400},
                ]
            }
            for i in range(1, 4)
        ]
        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_resp = MagicMock()
            mock_resp.text = '{"status": "pass", "scores": {"coverage": 1.0, "density": 1.0, "length": 1.0}}'
            mock_client.models.generate_content.return_value = mock_resp

            res_pass = giam_sat_quy_mo(
                chu_de="Tây Du Ký",
                final_chapters=mock_chapters_heavy,
                quy_mo="can_ban",
                api_keys=["mock_key"],
                so_chuong_yeu_cau=3
            )
            self.assertEqual(res_pass["status"], "pass")

if __name__ == "__main__":
    unittest.main()
