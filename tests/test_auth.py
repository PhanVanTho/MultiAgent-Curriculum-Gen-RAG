# -*- coding: utf-8 -*-
import os
import unittest
import sys
from datetime import datetime, timedelta
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

from ung_dung import app, db
from mo_hinh import NguoiDung, XacThucOTP, GoiCuoc

class TestAuthAndRBAC(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret-key"
        
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Reinitialize SQLAlchemy on this app to point to in-memory DB
        if "sqlalchemy" in app.extensions:
            del app.extensions["sqlalchemy"]
            
        # Bypass Flask setup lock
        app._got_first_request = False
        db.init_app(app)
        
        db.session.remove()
        db.create_all()
        
        self.client = app.test_client()
        self.seed_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def seed_data(self):
        from werkzeug.security import generate_password_hash
        hashed_pw = generate_password_hash("admin123")
        self.admin = NguoiDung(
            ten_dang_nhap="admin",
            mat_khau=hashed_pw,
            la_admin=True,
            email="admin@local",
            token=100
        )
        db.session.add(self.admin)
        
        hashed_user_pw = generate_password_hash("user123")
        self.user = NguoiDung(
            ten_dang_nhap="user",
            mat_khau=hashed_user_pw,
            la_admin=False,
            email="user@local",
            token=10
        )
        db.session.add(self.user)
        
        db.session.commit()

    def test_login_logout(self):
        # Test valid login
        resp = self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("user", resp.data.decode("utf-8"))
        
        # Test invalid login
        resp_invalid = self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "wrongpass"
        }, follow_redirects=True)
        self.assertIn("không đúng", resp_invalid.data.decode("utf-8"))
        
        # Test logout
        resp_logout = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(resp_logout.status_code, 200)

    def test_registration_and_otp_flow(self):
        # Register user with mock email OTP sending
        with patch("dich_vu.email_service.gui_email_otp") as mock_email:
            mock_email.return_value = (True, "Mock sent")
            
            resp = self.client.post("/register", data={
                "ten_dang_nhap": "newuser",
                "mat_khau": "newpass",
                "email": "newuser@local"
            }, follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            mock_email.assert_called_once()
            
            # OTP must be generated in DB
            otp_record = XacThucOTP.query.filter_by(email="newuser@local").first()
            self.assertIsNotNone(otp_record)
            self.assertEqual(otp_record.ten_dang_nhap, "newuser")
            
            # Test OTP verification - Incorrect OTP
            resp_verify_fail = self.client.post("/verify-otp", data={
                "otp": "000000"
            }, follow_redirects=True)
            self.assertIn("không chính xác", resp_verify_fail.data.decode("utf-8"))
            
            # Test OTP verification - Correct OTP
            # Set email in session to simulate register redirection state
            with self.client.session_transaction() as sess:
                sess["pending_register_email"] = "newuser@local"
                
            resp_verify_success = self.client.post("/verify-otp", data={
                "otp": otp_record.otp
            }, follow_redirects=True)
            
            self.assertIn("thành công", resp_verify_success.data.decode("utf-8"))
            
            # Check user is created in database
            new_user_db = NguoiDung.query.filter_by(ten_dang_nhap="newuser").first()
            self.assertIsNotNone(new_user_db)
            self.assertEqual(new_user_db.email, "newuser@local")

    def test_resend_otp(self):
        # Register first
        with patch("dich_vu.email_service.gui_email_otp") as mock_email:
            mock_email.return_value = (True, "Mock sent")
            self.client.post("/register", data={
                "ten_dang_nhap": "testresend",
                "mat_khau": "testpass",
                "email": "testresend@local"
            })
            
            # Simulate redirect session
            with self.client.session_transaction() as sess:
                sess["pending_register_email"] = "testresend@local"
            
            # Trigger resend-otp
            resp_resend = self.client.get("/resend-otp", follow_redirects=True)
            self.assertEqual(resp_resend.status_code, 200)
            
            # There should be 2 OTP records, the first marked as used/disabled, the second is active
            otps = XacThucOTP.query.filter_by(email="testresend@local").all()
            self.assertEqual(len(otps), 2)
            self.assertTrue(otps[0].da_dung)
            self.assertFalse(otps[1].da_dung)

    def test_forgot_and_reset_password(self):
        with patch("dich_vu.email_service.gui_email_otp") as mock_email:
            mock_email.return_value = (True, "Mock sent")
            
            # Forgot password request
            resp_forgot = self.client.post("/forgot-password", data={
                "email": "user@local"
            }, follow_redirects=True)
            self.assertEqual(resp_forgot.status_code, 200)
            mock_email.assert_called_once()
            
            otp_record = XacThucOTP.query.filter_by(email="user@local").first()
            self.assertIsNotNone(otp_record)
            
            # Reset password
            with self.client.session_transaction() as sess:
                sess["pending_reset_email"] = "user@local"
                
            resp_reset = self.client.post("/reset-password", data={
                "otp": otp_record.otp,
                "mat_khau_moi": "newuserpass",
                "xac_nhan_mat_khau_moi": "newuserpass"
            }, follow_redirects=True)
            
            self.assertIn("thành công", resp_reset.data.decode("utf-8"))
            
            # Verify login with new password
            resp_login = self.client.post("/login", data={
                "ten_dang_nhap": "user",
                "mat_khau": "newuserpass"
            }, follow_redirects=True)
            with self.client.session_transaction() as sess:
                flashes = sess.get("_flashes", [])
                self.assertTrue(any("Đăng nhập thành công" in f[1] for f in flashes))


    def test_rbac_authorization(self):
        # Access admin page when not logged in -> redirect to login
        resp_anon = self.client.get("/admin", follow_redirects=True)
        self.assertIn("Đăng nhập", resp_anon.data.decode("utf-8"))
        
        # Access admin page when logged in as normal user -> forbidden redirect to home
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })
        resp_user = self.client.get("/admin", follow_redirects=True)
        with self.client.session_transaction() as sess:
            flashes = sess.get("_flashes", [])
            self.assertTrue(any("Bạn không có quyền truy cập trang này" in f[1] for f in flashes))
        self.client.get("/logout")
        
        # Access admin page when logged in as admin -> success
        self.client.post("/login", data={
            "ten_dang_nhap": "admin",
            "mat_khau": "admin123"
        })
        resp_admin = self.client.get("/admin")
        self.assertEqual(resp_admin.status_code, 200)

    @patch("requests.get")
    def test_google_auth(self, mock_get):
        from cau_hinh import CauHinh
        original_google_client_id = CauHinh.GOOGLE_CLIENT_ID
        mock_client_id = "mock-google-client-id"
        CauHinh.GOOGLE_CLIENT_ID = mock_client_id
        app.config["GOOGLE_CLIENT_ID"] = mock_client_id
        
        try:
            # Mock Google Token Verification response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "sub": "google_12345",
                "email": "googleuser@local",
                "name": "Google User",
                "picture": "http://photo",
                "aud": mock_client_id
            }
            mock_get.return_value = mock_response
            
            # Post mock GIS credential to /auth/google
            resp = self.client.post("/auth/google", json={
                "credential": "mock_id_token"
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            
            # Since user google_12345 does not exist, redirect to register with info stored in session
            self.assertFalse(data["success"])
            self.assertTrue(data["need_register"])
            
            # Simulate registration completion for Google account
            with self.client.session_transaction() as sess:
                self.assertEqual(sess["google_pending"]["google_id"], "google_12345")
                self.assertEqual(sess["google_pending"]["email"], "googleuser@local")
                
            # Register using google details
            with patch("dich_vu.email_service.gui_email_otp") as mock_email:
                mock_email.return_value = (True, "Sent")
                self.client.post("/register", data={
                    "ten_dang_nhap": "googleuser",
                    "mat_khau": "googlesecret",
                    "email": "googleuser@local"
                })
                
                otp_record = XacThucOTP.query.filter_by(email="googleuser@local").first()
                with self.client.session_transaction() as sess:
                    sess["pending_register_email"] = "googleuser@local"
                    
                self.client.post("/verify-otp", data={"otp": otp_record.otp})
                
            # Post Google Sign-In again -> Should succeed and login
            resp_again = self.client.post("/auth/google", json={
                "credential": "mock_id_token"
            })
            self.assertEqual(resp_again.status_code, 200)
            data_again = resp_again.get_json()
            self.assertTrue(data_again["success"])
        finally:
            CauHinh.GOOGLE_CLIENT_ID = original_google_client_id

    @patch("requests.get")
    def test_google_auth_linking_existing_account(self, mock_get):
        from cau_hinh import CauHinh
        original_google_client_id = CauHinh.GOOGLE_CLIENT_ID
        mock_client_id = "mock-google-client-id"
        CauHinh.GOOGLE_CLIENT_ID = mock_client_id
        app.config["GOOGLE_CLIENT_ID"] = mock_client_id
        
        try:
            # 1. Mock Google Token Verification response for a new Google User
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "sub": "new_google_id_6789",
                "email": "different_google_email@local",
                "name": "Different Google User",
                "picture": "http://photo",
                "aud": mock_client_id
            }
            mock_get.return_value = mock_response
            
            # 2. Post mock GIS credential to /auth/google
            resp = self.client.post("/auth/google", json={
                "credential": "mock_id_token"
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertFalse(data["success"])
            self.assertTrue(data["need_register"])
            
            # Now we have google_pending in session.
            # 3. Log in with an existing username/password (e.g. 'user' / 'user123')
            resp_login = self.client.post("/login", data={
                "ten_dang_nhap": "user",
                "mat_khau": "user123"
            }, follow_redirects=True)
            self.assertEqual(resp_login.status_code, 200)
            
            # Verify that the existing 'user' account in DB has been auto-linked to "new_google_id_6789"
            user_db = NguoiDung.query.filter_by(ten_dang_nhap="user").first()
            self.assertEqual(user_db.google_id, "new_google_id_6789")
            self.assertEqual(user_db.ho_ten, "Different Google User")
            
            # Verify google_pending session is popped
            with self.client.session_transaction() as sess:
                self.assertNotIn("google_pending", sess)
        finally:
            CauHinh.GOOGLE_CLIENT_ID = original_google_client_id

    def test_profile_update_username(self):
        # Log in as user
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })
        
        # Test editing username to 'newusername'
        resp = self.client.post("/profile", data={
            "ten_dang_nhap": "newusername",
            "ho_ten": "User Updated",
            "email": "user@local"
        }, follow_redirects=True)
        
        # Verify db updated
        user_updated = NguoiDung.query.filter_by(email="user@local").first()
        self.assertEqual(user_updated.ten_dang_nhap, "newusername")
        
        # Test editing to a username that contains spaces (should fail validation)
        self.client.post("/profile", data={
            "ten_dang_nhap": "new username",
            "ho_ten": "User Updated",
            "email": "user@local"
        }, follow_redirects=True)
        user_updated = NguoiDung.query.filter_by(email="user@local").first()
        self.assertEqual(user_updated.ten_dang_nhap, "newusername")  # Still 'newusername'
        
        # Test editing to an existing username 'admin' (should fail uniqueness validation)
        self.client.post("/profile", data={
            "ten_dang_nhap": "admin",
            "ho_ten": "User Updated",
            "email": "user@local"
        }, follow_redirects=True)
        user_updated = NguoiDung.query.filter_by(email="user@local").first()
        self.assertEqual(user_updated.ten_dang_nhap, "newusername")  # Still 'newusername'

    def test_chatbot_api(self):
        # 1. Anonymous access should redirect to login
        resp_anon_history = self.client.get("/api/chat/history")
        self.assertEqual(resp_anon_history.status_code, 302)

        resp_anon_chat = self.client.post("/api/chat", json={"message": "hello"})
        self.assertEqual(resp_anon_chat.status_code, 302)

        # 2. Login
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })

        # 3. Test chatbot history is empty initially
        resp_history = self.client.get("/api/chat/history")
        self.assertEqual(resp_history.status_code, 200)
        data = resp_history.get_json()
        self.assertEqual(len(data.get("history", [])), 0)

        # 4. Mock OpenAI completion and call /api/chat
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content="Đây là câu trả lời thử nghiệm."))
            ]

            resp_chat = self.client.post("/api/chat", json={"message": "Câu hỏi thử nghiệm"})
            self.assertEqual(resp_chat.status_code, 200)
            chat_data = resp_chat.get_json()
            self.assertEqual(chat_data.get("reply"), "Đây là câu trả lời thử nghiệm.")

            # Check that history now has 2 messages (1 user, 1 bot)
            resp_history_after = self.client.get("/api/chat/history")
            self.assertEqual(resp_history_after.status_code, 200)
            history_data = resp_history_after.get_json()
            messages = history_data.get("history", [])
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0]["role"], "user")
            self.assertEqual(messages[0]["content"], "Câu hỏi thử nghiệm")
            self.assertEqual(messages[1]["role"], "assistant")
            self.assertEqual(messages[1]["content"], "Đây là câu trả lời thử nghiệm.")

if __name__ == "__main__":
    unittest.main()
