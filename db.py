import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def get_connection():
    """Hàm dùng chung để mở kết nối DB, tránh lặp code ở nhiều nơi"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )