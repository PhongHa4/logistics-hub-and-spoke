import os
from dotenv import load_dotenv
import psycopg2

# Đọc thông tin từ file .env
load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    print("✅ Kết nối thành công tới logistics_db!")

    # Test thử một query đơn giản
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ways;")
    count = cur.fetchone()[0]
    print(f"Số lượng way trong bảng: {count}")

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Kết nối thất bại:", e)