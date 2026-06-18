# -*- coding: utf-8 -*-
import os
import unittest
import sys
import json
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
from mo_hinh import NguoiDung, GoiCuoc, LichSuGiaoTrinh

class TestAdminDashboard(unittest.TestCase):
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
        
        # 1. Admin user
        self.admin_user = NguoiDung(
            ten_dang_nhap="admin",
            mat_khau=generate_password_hash("admin123"),
            la_admin=True,
            email="admin@local",
            token=100
        )
        db.session.add(self.admin_user)
        
        # 2. Regular user
        self.regular_user = NguoiDung(
            ten_dang_nhap="user",
            mat_khau=generate_password_hash("user123"),
            la_admin=False,
            email="user@local",
            token=10
        )
        db.session.add(self.regular_user)
        db.session.flush()
        
        # 3. Test packages
        self.package = GoiCuoc(
            ten_goi="Gói Test",
            gia_tien=10000,
            so_token=10,
            kich_hoat=True
        )
        db.session.add(self.package)
        
        # 4. Test curriculum
        self.curriculum = LichSuGiaoTrinh(
            chu_de="Giáo trình Python",
            nguoi_dung_id=self.regular_user.id,
            noi_dung_html="<p>Python</p>",
            ngay_tao=None
        )
        db.session.add(self.curriculum)
        db.session.commit()

    def test_admin_route_authorization(self):
        # 1. Anonymous user accesses admin dashboard -> redirects to login
        for path in ["/admin/users", "/admin/curriculums", "/admin/settings", "/admin/packages"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 302)
            
        # 2. Regular user accesses admin dashboard -> redirects (returns 302 or flashes unauthorized)
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })
        for path in ["/admin/settings", "/admin/packages"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 302)
            
        self.client.get("/logout")
        
        # 3. Admin user accesses admin pages -> 200 OK
        self.client.post("/login", data={
            "ten_dang_nhap": "admin",
            "mat_khau": "admin123"
        })
        for path in ["/admin/users", "/admin/curriculums", "/admin/settings", "/admin/packages"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200)

    def test_toggle_block_user(self):
        self.client.post("/login", data={
            "ten_dang_nhap": "admin",
            "mat_khau": "admin123"
        })
        
        # Initial status is not blocked
        self.assertFalse(self.regular_user.bi_khoa)
        
        # Toggle block
        resp = self.client.post("/admin/toggle_block_user", json={
            "user_id": self.regular_user.id
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])
        
        db.session.refresh(self.regular_user)
        self.assertTrue(self.regular_user.bi_khoa)
        
        # Toggle back
        resp_back = self.client.post("/admin/toggle_block_user", json={
            "user_id": self.regular_user.id
        })
        self.assertEqual(resp_back.status_code, 200)
        self.assertTrue(resp_back.get_json()["success"])
        
        db.session.refresh(self.regular_user)
        self.assertFalse(self.regular_user.bi_khoa)

    def test_delete_user(self):
        self.client.post("/login", data={
            "ten_dang_nhap": "admin",
            "mat_khau": "admin123"
        })
        
        # Test delete regular user
        user_id = self.regular_user.id
        resp = self.client.post("/admin/delete_user", json={"user_id": user_id})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])
        
        # Verify user is deleted
        deleted_user = db.session.get(NguoiDung, user_id)
        self.assertIsNone(deleted_user)
        
        # Test cannot delete self
        admin_id = self.admin_user.id
        resp_self = self.client.post("/admin/delete_user", json={"user_id": admin_id})
        self.assertEqual(resp_self.status_code, 400)
        self.assertFalse(resp_self.get_json()["success"])

    def test_admin_update_user_password(self):
        from werkzeug.security import check_password_hash
        self.client.post("/login", data={
            "ten_dang_nhap": "admin",
            "mat_khau": "admin123"
        })
        
        # Update user password
        resp = self.client.post("/admin/update_user", json={
            "id": self.regular_user.id,
            "ho_ten": "Updated Name",
            "email": "updated@local",
            "token": 50,
            "la_admin": False,
            "mat_khau": "newsecurepassword123"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])
        
        db.session.refresh(self.regular_user)
        self.assertEqual(self.regular_user.ho_ten, "Updated Name")
        self.assertEqual(self.regular_user.email, "updated@local")
        self.assertEqual(self.regular_user.token, 50)
        self.assertTrue(check_password_hash(self.regular_user.mat_khau, "newsecurepassword123"))

    def test_package_management(self):
        self.client.post("/login", data={
            "ten_dang_nhap": "admin",
            "mat_khau": "admin123"
        })
        
        # 1. Add package
        resp_add = self.client.post("/admin/packages/save", data={
            "ten_goi": "Gói Mới",
            "gia_tien": 30000,
            "so_token": 50,
            "mo_ta": "Mô tả gói mới",
            "kich_hoat": "on"
        })
        self.assertEqual(resp_add.status_code, 302)
        
        new_pkg = GoiCuoc.query.filter_by(ten_goi="Gói Mới").first()
        self.assertIsNotNone(new_pkg)
        self.assertEqual(new_pkg.gia_tien, 30000)
        self.assertEqual(new_pkg.so_token, 50)
        
        # 2. Toggle package active status
        pkg_id = new_pkg.id
        self.assertTrue(new_pkg.kich_hoat)
        
        resp_toggle = self.client.post(f"/admin/packages/toggle/{pkg_id}")
        self.assertEqual(resp_toggle.status_code, 200)
        self.assertTrue(resp_toggle.get_json()["success"])
        
        db.session.refresh(new_pkg)
        self.assertFalse(new_pkg.kich_hoat)
        
        # 3. Delete package
        resp_del = self.client.post(f"/admin/packages/delete/{pkg_id}")
        self.assertEqual(resp_del.status_code, 200)
        self.assertTrue(resp_del.get_json()["success"])
        
        deleted_pkg = GoiCuoc.query.get(pkg_id)
        self.assertIsNone(deleted_pkg)

    @patch("dotenv.set_key")
    def test_update_settings(self, mock_set_key):
        self.client.post("/login", data={
            "ten_dang_nhap": "admin",
            "mat_khau": "admin123"
        })
        
        # Test update config setting
        resp = self.client.post("/admin/update_settings", json={
            "OPENAI_MODEL": "gpt-4o-mini-test-admin",
            "PHI_TOKEN_AUTO": 5,
            "PHI_TOKEN_EXPERT": 10,
            "PHI_TOKEN_CREATIVE": 15
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])
        
        # Assert dotenv.set_key was called to save on disk
        self.assertTrue(mock_set_key.called)
        
        # Assert in-memory CauHinh was updated
        from cau_hinh import CauHinh
        self.assertEqual(CauHinh.OPENAI_MODEL, "gpt-4o-mini-test-admin")
        self.assertEqual(CauHinh.PHI_TOKEN_AUTO, 5)
        self.assertEqual(CauHinh.PHI_TOKEN_EXPERT, 10)
        self.assertEqual(CauHinh.PHI_TOKEN_CREATIVE, 15)

    def test_user_delete_curriculum(self):
        # 1. Anonymous user cannot delete
        resp = self.client.post(f"/lich-su/xoa/{self.curriculum.id}")
        self.assertEqual(resp.status_code, 302)

        # 2. Login as regular_user (owner)
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })

        # Try to delete own curriculum
        resp = self.client.post(f"/lich-su/xoa/{self.curriculum.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])
        
        # Verify from database
        deleted_item = db.session.get(LichSuGiaoTrinh, self.curriculum.id)
        self.assertIsNone(deleted_item)

        # Logout
        self.client.get("/logout")

        # 3. Create another curriculum for admin
        admin_curr = LichSuGiaoTrinh(
            chu_de="Giáo trình Admin",
            nguoi_dung_id=self.admin_user.id,
            noi_dung_html="<p>Admin only</p>"
        )
        db.session.add(admin_curr)
        db.session.commit()

        # Login as regular user
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })

        # Try to delete admin's curriculum -> Should return 403
        resp = self.client.post(f"/lich-su/xoa/{admin_curr.id}")
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(resp.get_json()["success"])

        # Logout
        self.client.get("/logout")

        # 4. Test delete in-memory temporary job (failed status)
        from ung_dung import CONG_VIEC
        CONG_VIEC["test_job_123"] = {
            "user_id": self.regular_user.id,
            "trang_thai": "that_bai",
            "chu_de": "Failed Job"
        }

        # Login as regular user
        self.client.post("/login", data={
            "ten_dang_nhap": "user",
            "mat_khau": "user123"
        })

        # Delete failed temporary job -> Should return 200
        resp = self.client.post("/lich-su/xoa-luu-tam/test_job_123")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])
        self.assertNotIn("test_job_123", CONG_VIEC)

if __name__ == "__main__":
    unittest.main()
