import os
from flask_login import UserMixin
from datetime import datetime

if os.getenv("DB_USE_SQLITE") == "True":
    db_type = "sqlite"
else:
    db_type = os.getenv("DB_TYPE", "mysql").lower()

if db_type == "mongodb":
    from mongosql_compat import MongoSQLAlchemy
    db = MongoSQLAlchemy()
    LONGTEXT = "LONGTEXT"
    mysql_INTEGER = db.Integer
else:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
    from sqlalchemy.dialects.mysql import LONGTEXT
    from sqlalchemy.dialects.mysql import INTEGER as mysql_INTEGER

class NguoiDung(UserMixin, db.Model):
    __tablename__ = 'nguoi_dung'
    id = db.Column(db.Integer, primary_key=True)
    ten_dang_nhap = db.Column(db.String(150), unique=True, nullable=False)
    mat_khau = db.Column("mat_khau_hash", db.String(255), nullable=True)
    la_admin = db.Column(db.Boolean, default=False)
    bi_khoa = db.Column(db.Boolean, default=False, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    ho_ten = db.Column(db.String(255), nullable=True)
    anh_dai_dien = db.Column(db.String(500), nullable=True)
    token = db.Column(db.Integer, default=10)
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ với bảng lịch sử
    lich_su = db.relationship('LichSuGiaoTrinh', backref='nguoi_dung', lazy=True)

class LichSuGiaoTrinh(db.Model):
    __tablename__ = 'lich_su_giao_trinh'
    id = db.Column(db.Integer, primary_key=True)
    nguoi_dung_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'), nullable=True)
    chu_de = db.Column(db.String(255), nullable=False)
    noi_dung_html = db.Column(db.Text().with_variant(LONGTEXT, "mysql")) # LongText in MySQL
    duong_dan_file = db.Column(db.String(255))
    do_dai_ky_tu = db.Column(db.Integer, default=0)
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)
    da_xuat_file = db.Column(db.Boolean, default=False)
    noi_bat = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def ma_cv(self):
        if self.duong_dan_file:
            # Assumes format: .../uuid.pdf
            import os
            basename = os.path.basename(self.duong_dan_file)
            return os.path.splitext(basename)[0]
        return None

    def __repr__(self):
        return f'<GiaoTrinh {self.chu_de}>'

class XacThucOTP(db.Model):
    __tablename__ = 'xac_thuc_otp'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    ten_dang_nhap = db.Column(db.String(150), nullable=False)
    mat_khau_hash = db.Column(db.String(255), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)
    het_han = db.Column(db.DateTime, nullable=False)
    da_dung = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(255), nullable=True)
    ho_ten = db.Column(db.String(255), nullable=True)
    anh_dai_dien = db.Column(db.String(500), nullable=True)
    nguoi_dung_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id', ondelete='CASCADE'), nullable=True)
    nguoi_dung = db.relationship('NguoiDung', backref='otps', lazy=True)

class GiaoDichNapToken(db.Model):
    __tablename__ = 'giao_dich_nap_token'
    id = db.Column(db.Integer, primary_key=True)
    ma_giao_dich = db.Column(db.String(100), unique=True, nullable=False)
    nguoi_dung_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'), nullable=False)
    so_tien = db.Column(db.Integer, nullable=False)
    so_token = db.Column(db.Integer, nullable=False)
    phuong_thuc = db.Column(db.String(50), nullable=False)
    trang_thai = db.Column(db.String(50), default='cho_thanh_toan')
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)
    ngay_hoan_thanh = db.Column(db.DateTime, nullable=True)
    goi_cuoc_id = db.Column(db.Integer, db.ForeignKey('goi_cuoc.id'), nullable=True)
    goi_cuoc = db.relationship('GoiCuoc', backref='giao_dich', lazy=True)

class GoiCuoc(db.Model):
    __tablename__ = 'goi_cuoc'
    id = db.Column(db.Integer, primary_key=True)
    ten_goi = db.Column(db.String(100), nullable=False)
    gia_tien = db.Column(db.Integer, nullable=False)
    so_token = db.Column(db.Integer, nullable=False)
    mo_ta = db.Column(db.String(500), nullable=True)
    kich_hoat = db.Column(db.Boolean, default=True, nullable=False)

class CauHinhHeThong(db.Model):
    __tablename__ = 'cau_hinh_he_thong'
    id = db.Column(db.Integer, primary_key=True)
    khoa = db.Column(db.String(100), unique=True, nullable=False)
    gia_tri = db.Column(db.Text, nullable=True)
    mo_ta = db.Column(db.String(255), nullable=True)
    ngay_cap_nhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LichSuChatbot(db.Model):
    __tablename__ = 'lich_su_chatbot'
    id = db.Column(db.Integer, primary_key=True)
    nguoi_dung_id = db.Column(db.Integer().with_variant(mysql_INTEGER(unsigned=True), "mysql"), db.ForeignKey('nguoi_dung.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)

class TrangThongTin(db.Model):
    __tablename__ = 'trang_thong_tin'
    id = db.Column(db.Integer, primary_key=True)
    ma_trang = db.Column(db.String(100), unique=True, nullable=False) # 'privacy-policy', 'terms-of-service', 'data-deletion', 'ai-terms'
    tieu_de_vi = db.Column(db.String(255), nullable=False)
    tieu_de_en = db.Column(db.String(255), nullable=False)
    mo_ta_vi = db.Column(db.String(500), nullable=True)
    mo_ta_en = db.Column(db.String(500), nullable=True)
    noi_dung_vi = db.Column(db.Text().with_variant(LONGTEXT, "mysql"))
    noi_dung_en = db.Column(db.Text().with_variant(LONGTEXT, "mysql"))
    ngay_cap_nhat = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)




