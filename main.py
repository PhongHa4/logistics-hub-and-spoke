import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import psycopg2

load_dotenv()

app = FastAPI(title="Logistics Hub-and-Spoke API")

def get_connection():
    """Hàm dùng chung để mở kết nối DB, tránh lặp code ở nhiều nơi"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

@app.get("/")
def health_check():
    """Endpoint kiểm tra API có đang chạy không"""
    return {"status": "ok", "message": "Logistics API đang chạy"}

@app.get("/ways/count")
def count_ways():
    """Endpoint test: đếm số way trong DB"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ways;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"total_ways": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))