import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from db import get_connection
import psycopg2
from routers.orders import router as orders_router
from routers.routes import router as routes_router
from time_matrix import compute_time_matrix
from fastapi.middleware.cors import CORSMiddleware
from routers.ws import router as ws_router

load_dotenv()

app = FastAPI(title="Logistics Hub-and-Spoke API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(orders_router)
app.include_router(routes_router)
app.include_router(ws_router)

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


@app.get("/matrix/test")
def get_test_matrix():
    """Endpoint test: tính ma trận thời gian giữa 5 điểm cố định"""
    node_ids = [81537, 949220, 1155520, 990865, 385191]
    try:
        matrix = compute_time_matrix(node_ids)
        return {"node_ids": node_ids, "matrix": matrix}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))