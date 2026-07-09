import random
from main import get_connection

# Tâm khu vực (dùng lại tọa độ đã thống nhất ở Mốc 2)
HANOI_CENTER = (105.8542, 21.0285)
HAIPHONG_CENTER = (106.6881, 20.8449)
HALONG_CENTER = (107.0797, 20.9515)

RADIUS_HANOI_M = 15000       # bán kính lấy shop quanh Hà Nội (15km)
RADIUS_DELIVERY_M = 10000    # bán kính lấy điểm giao quanh Hải Phòng + Hạ Long (10km mỗi nơi)

NUM_SHOPS = 40
NUM_DELIVERIES = 40


def get_candidate_vertices(cur, center_lng, center_lat, radius_m, limit=500):
    """Lấy danh sách đỉnh (id) nằm trong bán kính quanh 1 tâm tọa độ"""
    cur.execute("""
        SELECT id FROM ways_vertices_pgr
        WHERE ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s
        )
        LIMIT %s;
    """, (center_lng, center_lat, radius_m, limit))
    return [row[0] for row in cur.fetchall()]


def create_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mock_orders (
            id SERIAL PRIMARY KEY,
            node_id BIGINT NOT NULL,
            order_type VARCHAR(20) NOT NULL,  -- 'shop' hoặc 'delivery'
            demand_kg NUMERIC NOT NULL
        );
    """)
    cur.execute("TRUNCATE TABLE mock_orders;")  # xóa data cũ mỗi lần chạy lại cho sạch


def generate():
    conn = get_connection()
    cur = conn.cursor()

    create_table(cur)

    # --- Sinh shop quanh Hà Nội ---
    hanoi_candidates = get_candidate_vertices(cur, *HANOI_CENTER, RADIUS_HANOI_M)
    shop_nodes = random.sample(hanoi_candidates, min(NUM_SHOPS, len(hanoi_candidates)))

    for node_id in shop_nodes:
        demand = random.randint(3, 15)
        cur.execute(
            "INSERT INTO mock_orders (node_id, order_type, demand_kg) VALUES (%s, 'shop', %s);",
            (node_id, demand)
        )

    # --- Sinh điểm giao quanh Hải Phòng + Hạ Long (gộp chung vùng Hub B) ---
    hp_candidates = get_candidate_vertices(cur, *HAIPHONG_CENTER, RADIUS_DELIVERY_M)
    hl_candidates = get_candidate_vertices(cur, *HALONG_CENTER, RADIUS_DELIVERY_M)
    delivery_candidates = hp_candidates + hl_candidates
    delivery_nodes = random.sample(delivery_candidates, min(NUM_DELIVERIES, len(delivery_candidates)))

    for node_id in delivery_nodes:
        demand = random.randint(3, 15)
        cur.execute(
            "INSERT INTO mock_orders (node_id, order_type, demand_kg) VALUES (%s, 'delivery', %s);",
            (node_id, demand)
        )

    conn.commit()

    # --- Sanity check ---
    cur.execute("SELECT order_type, COUNT(*), SUM(demand_kg) FROM mock_orders GROUP BY order_type;")
    print("Kết quả sinh Mock Data:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} điểm, tổng demand = {row[2]}kg")

    cur.close()
    conn.close()


if __name__ == "__main__":
    generate()