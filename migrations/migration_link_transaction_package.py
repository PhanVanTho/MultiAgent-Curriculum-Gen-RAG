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
        print("=== RUNNING MIGRATION: LINK GIAO_DICH_NAP_TOKEN & GOI_CUOC ===")
        
        # Check if goi_cuoc_id already exists in giao_dich_nap_token
        cur.execute("SHOW COLUMNS FROM giao_dich_nap_token LIKE 'goi_cuoc_id'")
        result = cur.fetchone()
        
        if result:
            print("Cột 'goi_cuoc_id' đã tồn tại trong bảng 'giao_dich_nap_token'. Bỏ qua di trú cột.")
        else:
            print("Đang thêm cột 'goi_cuoc_id' và thiết lập khóa ngoại liên kết tới 'goi_cuoc'...")
            # 1. Add column
            cur.execute("ALTER TABLE giao_dich_nap_token ADD COLUMN goi_cuoc_id INT NULL")
            # 2. Add foreign key constraint
            cur.execute("ALTER TABLE giao_dich_nap_token ADD CONSTRAINT fk_giao_dich_goi_cuoc FOREIGN KEY (goi_cuoc_id) REFERENCES goi_cuoc(id) ON DELETE SET NULL")
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
