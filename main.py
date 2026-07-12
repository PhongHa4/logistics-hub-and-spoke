import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from db import get_connection
import psycopg2
from routers.orders import router as orders_router

load_dotenv()

app = FastAPI(title="Logistics Hub-and-Spoke API")
app.include_router(orders_router)

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

def compute_time_matrix(node_ids: list[int]) -> list[list[float]]:
    """
    Tính ma trận thời gian di chuyển (giây) giữa các điểm trong node_ids.
    Trả về ma trận vuông n x n, matrix[i][j] = thời gian từ node_ids[i] đến node_ids[j].
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM pgr_dijkstraCostMatrix(
            'SELECT id, source, target,
                    cost_s * peak_factor AS cost,
                    reverse_cost_s * peak_factor AS reverse_cost
             FROM ways',
            %s,
            directed := true
        );
    """, (node_ids,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    n = len(node_ids)
    index_map = {node_id: i for i, node_id in enumerate(node_ids)}
    matrix = [[0] * n for _ in range(n)]

    for start_vid, end_vid, agg_cost in rows:
        i = index_map[start_vid]
        j = index_map[end_vid]
        matrix[i][j] = agg_cost

    return matrix


@app.get("/matrix/test")
def get_test_matrix():
    """Endpoint test: tính ma trận thời gian giữa 5 điểm cố định"""
    node_ids = [81537, 949220, 1155520, 990865, 385191]
    try:
        matrix = compute_time_matrix(node_ids)
        return {"node_ids": node_ids, "matrix": matrix}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))