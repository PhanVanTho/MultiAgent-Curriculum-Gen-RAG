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
from mo_hinh import NguoiDung, GiaoDichNapToken, GoiCuoc
from dich_vu.sepay import encode_payment_id, decode_payment_id

class TestPaymentAndSubscriptions(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret-key"
        
        self.app_context = app.app_context()
        self.app_context.push()
        
        if "sqlalchemy" in app.extensions:
            del app.extensions["sqlalchemy"]
            
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
        hashed_user_pw = generate_password_hash("user123")
        self.user = NguoiDung(
            ten_dang_nhap="user",
            mat_khau=hashed_user_pw,
            la_admin=False,
            email="user@local",
            token=10
        )
        db.session.add(self.user)
        
        self.package = GoiCuoc(
            ten_goi="Gói Vàng",
            gia_tien=50000,
            so_token=500,
            kich_hoat=True
        )
        db.session.add(self.package)
        
        db.session.commit()

    def test_buy_tokens_page(self):
        # Access pricing page when not logged in -> redirect
        resp_anon = self.client.get("/buy-tokens")
        self.assertEqual(resp_anon.status_code, 302)
        
        # Log in
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })
        
        # Access page -> Should show the seeded package
        resp_user = self.client.get("/buy-tokens")
        self.assertEqual(resp_user.status_code, 200)
        self.assertIn("Gói Vàng", resp_user.data.decode("utf-8"))
        self.assertIn("50,000", resp_user.data.decode("utf-8"))

    def test_create_payment_transaction(self):
        # Log in
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })
        
        # Create payment via SEPAY
        resp = self.client.post("/payment/create", data={
            "tokens": 500,
            "price": 50000,
            "package_name": "Gói Vàng",
            "method": "SEPAY",
            "goi_cuoc_id": self.package.id
        }, follow_redirects=False)
        
        # Check redirect to checkout
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/payment/sepay/", resp.location)
        
        # Verify transaction is created in DB
        txn = GiaoDichNapToken.query.filter_by(nguoi_dung_id=self.user.id).first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.so_token, 500)
        self.assertEqual(txn.so_tien, 50000)
        self.assertEqual(txn.trang_thai, "cho_thanh_toan")
        self.assertEqual(txn.phuong_thuc, "SEPAY")

    def test_sepay_checkout_page(self):
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })
        
        # Create a transaction
        txn = GiaoDichNapToken(
            ma_giao_dich="test_sepay_txn",
            nguoi_dung_id=self.user.id,
            so_tien=50000,
            so_token=500,
            phuong_thuc="SEPAY",
            trang_thai="cho_thanh_toan",
            goi_cuoc_id=self.package.id
        )
        db.session.add(txn)
        db.session.commit()
        
        # Access checkout page
        resp = self.client.get(f"/payment/sepay/{txn.id}")
        self.assertEqual(resp.status_code, 200)
        
        hex_id = encode_payment_id(txn.id)
        # Content should show QR or transfer content containing the HEX code
        self.assertIn(hex_id, resp.data.decode("utf-8"))

    def test_encode_decode_payment_id(self):
        test_id = 9999
        encoded = encode_payment_id(test_id)
        self.assertTrue(isinstance(encoded, str))
        
        decoded = decode_payment_id(encoded)
        self.assertEqual(decoded, test_id)

    @patch("dich_vu.sepay.get_last_transactions")
    def test_sepay_status_polling(self, mock_get_last):
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })
        
        # Create a transaction
        txn = GiaoDichNapToken(
            ma_giao_dich="test_polling_txn",
            nguoi_dung_id=self.user.id,
            so_tien=50000,
            so_token=500,
            phuong_thuc="SEPAY",
            trang_thai="cho_thanh_toan",
            goi_cuoc_id=self.package.id
        )
        db.session.add(txn)
        db.session.commit()
        
        # 1. Before payment, status is pending
        mock_get_last.return_value = []
        resp_pending = self.client.get(f"/api/payment/sepay/status/{txn.id}")
        self.assertEqual(resp_pending.status_code, 200)
        self.assertEqual(resp_pending.get_json()["status"], "pending")
        
        # 2. Simulate bank transaction matching
        from cau_hinh import CauHinh
        hex_id = encode_payment_id(txn.id)
        mock_get_last.return_value = [
            {
                "content": f"{CauHinh.SEPAY_WEB_NAME}NAPTOKEN{hex_id}",
                "amount_in": "50000"
            }
        ]
        
        resp_completed = self.client.get(f"/api/payment/sepay/status/{txn.id}")
        self.assertEqual(resp_completed.status_code, 200)
        self.assertEqual(resp_completed.get_json()["status"], "completed")
        
        # Check DB states
        db.session.refresh(txn)
        self.assertEqual(txn.trang_thai, "thanh_cong")
        
        db.session.refresh(self.user)
        self.assertEqual(self.user.token, 510) # 10 original + 500 new

    @patch("dich_vu.vnpay.VNPay.verify_payment")
    def test_vnpay_callback(self, mock_verify):
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })
        
        # Create a transaction
        txn = GiaoDichNapToken(
            ma_giao_dich="test_vnpay_txn",
            nguoi_dung_id=self.user.id,
            so_tien=50000,
            so_token=500,
            phuong_thuc="VNPAY",
            trang_thai="cho_thanh_toan",
            goi_cuoc_id=self.package.id
        )
        db.session.add(txn)
        db.session.commit()
        
        # 1. Signature invalid
        mock_verify.return_value = False
        resp_invalid = self.client.get("/payment/callback", query_string={
            "vnp_TxnRef": "test_vnpay_txn",
            "vnp_ResponseCode": "00"
        }, follow_redirects=True)
        self.assertIn("Chữ ký không hợp lệ", resp_invalid.data.decode("utf-8"))
        
        # 2. Signature valid and ResponseCode success
        mock_verify.return_value = True
        resp_success = self.client.get("/payment/callback", query_string={
            "vnp_TxnRef": "test_vnpay_txn",
            "vnp_ResponseCode": "00"
        }, follow_redirects=True)
        self.assertIn("thành công", resp_success.data.decode("utf-8"))
        
        db.session.refresh(txn)
        self.assertEqual(txn.trang_thai, "thanh_cong")
        
        db.session.refresh(self.user)
        self.assertEqual(self.user.token, 510)

    @patch("dich_vu.email_service.gui_email_thanh_toan_thanh_cong")
    def test_sepay_webhook(self, mock_send_email):
        # Create a transaction
        txn = GiaoDichNapToken(
            ma_giao_dich="sepay_webhook_txn",
            nguoi_dung_id=self.user.id,
            so_tien=50000,
            so_token=500,
            phuong_thuc="SEPAY",
            trang_thai="cho_thanh_toan",
            goi_cuoc_id=self.package.id
        )
        db.session.add(txn)
        db.session.commit()
        
        # Test 1: Unauthorized webhook
        from cau_hinh import CauHinh
        old_sepay_key = CauHinh.SEPAY_API_KEY
        CauHinh.SEPAY_API_KEY = "test_key"
        
        resp = self.client.post("/api/payment/sepay/webhook", json={
            "content": f"{CauHinh.SEPAY_WEB_NAME}NAPTOKEN{encode_payment_id(txn.id)}",
            "amountIn": 50000
        }, headers={"Authorization": "Bearer invalid_key"})
        self.assertEqual(resp.status_code, 401)
        
        # Test 2: Authorized success
        resp_success = self.client.post("/api/payment/sepay/webhook", json={
            "content": f"{CauHinh.SEPAY_WEB_NAME}NAPTOKEN{encode_payment_id(txn.id)}",
            "amountIn": 50000
        }, headers={"Authorization": "Bearer test_key"})
        self.assertEqual(resp_success.status_code, 200)
        self.assertEqual(resp_success.get_json()["status"], "success")
        
        db.session.refresh(txn)
        self.assertEqual(txn.trang_thai, "thanh_cong")
        
        db.session.refresh(self.user)
        self.assertEqual(self.user.token, 510)
        
        # Verify email is called
        mock_send_email.assert_called_once()
        
        # Restore key
        CauHinh.SEPAY_API_KEY = old_sepay_key

    @patch("dich_vu.vnpay.VNPay.verify_payment")
    @patch("dich_vu.email_service.gui_email_thanh_toan_thanh_cong")
    def test_vnpay_ipn(self, mock_send_email, mock_verify):
        # Create a transaction
        txn = GiaoDichNapToken(
            ma_giao_dich="vnpay_ipn_txn",
            nguoi_dung_id=self.user.id,
            so_tien=50000,
            so_token=500,
            phuong_thuc="VNPAY",
            trang_thai="cho_thanh_toan",
            goi_cuoc_id=self.package.id
        )
        db.session.add(txn)
        db.session.commit()
        
        # 1. Invalid signature
        mock_verify.return_value = False
        resp = self.client.get("/payment/vnpay_ipn", query_string={
            "vnp_TxnRef": "vnpay_ipn_txn",
            "vnp_ResponseCode": "00",
            "vnp_Amount": "5000000"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["RspCode"], "97")
        
        # 2. Valid and success
        mock_verify.return_value = True
        resp_success = self.client.get("/payment/vnpay_ipn", query_string={
            "vnp_TxnRef": "vnpay_ipn_txn",
            "vnp_ResponseCode": "00",
            "vnp_Amount": "5000000"
        })
        self.assertEqual(resp_success.status_code, 200)
        self.assertEqual(resp_success.get_json()["RspCode"], "00")
        
        db.session.refresh(txn)
        self.assertEqual(txn.trang_thai, "thanh_cong")
        
        db.session.refresh(self.user)
        self.assertEqual(self.user.token, 510)
        mock_send_email.assert_called_once()

if __name__ == "__main__":
    unittest.main()

