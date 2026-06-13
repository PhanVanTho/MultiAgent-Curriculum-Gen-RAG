# -*- coding: utf-8 -*-
import pymysql
from dotenv import load_dotenv
import os
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def run_migration():
    conn = pymysql.connect(
        host="127.0.0.1",
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "giao_trinh_ai"),
        port=int(os.getenv("DB_PORT", "3306")),
        charset='utf8mb4'
    )
    cur = conn.cursor()
    
    try:
        print("=== RUNNING MIGRATION: LINK XAC_THUC_OTP & NGUOI_DUNG ===")
        
        # Check if nguoi_dung_id already exists in xac_thuc_otp
        cur.execute("SHOW COLUMNS FROM xac_thuc_otp LIKE 'nguoi_dung_id'")
        result = cur.fetchone()
        
        if result:
            print("Cột 'nguoi_dung_id' đã tồn tại trong bảng 'xac_thuc_otp'. Bỏ qua di trú cột.")
        else:
            print("Đang thêm cột 'nguoi_dung_id' (nullable) và thiết lập khóa ngoại liên kết tới 'nguoi_dung'...")
            # 1. Add column matched with nguoi_dung.id (int unsigned)
            cur.execute("ALTER TABLE xac_thuc_otp ADD COLUMN nguoi_dung_id INT(10) UNSIGNED NULL")
            # 2. Add foreign key constraint with ON DELETE CASCADE
            cur.execute("ALTER TABLE xac_thuc_otp ADD CONSTRAINT fk_otp_nguoi_dung FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id) ON DELETE CASCADE")
            print("Đã thêm cột và thiết lập khóa ngoại thành công!")
            
        conn.commit()
        print("Di trú cơ sở dữ liệu hoàn tất thành công!")
        
    except Exception as e:
        conn.rollback()
        print(f"Lỗi di trú: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
