from main import get_connection
from geo_constants import (
    HANOI_CENTER, HAIPHONG_CENTER, HALONG_CENTER,
    RADIUS_HANOI_M, RADIUS_DELIVERY_M, NEAREST_NODE_RADIUS_M,
)


def find_nearest_node(lng: float, lat: float, radius_m: int = NEAREST_NODE_RADIUS_M) -> int | None:
    """
    Tìm node_id gần nhất trên ways_vertices_pgr trong bán kính radius_m.
    Trả về None nếu không tìm thấy node nào trong bán kính (nghi ngờ geocode sai
    hoặc địa chỉ nằm ngoài vùng dữ liệu OSM đã cắt - tam giác HN-HP-QN).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM ways_vertices_pgr
        WHERE ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s
        )
        ORDER BY geom::geography <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
        LIMIT 1;
    """, (lng, lat, radius_m, lng, lat))

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def classify_hub_zone(lng: float, lat: float) -> str | None:
    """
    Xác định 1 điểm tọa độ thuộc vùng phủ của Hub nào.
    Trả về 'hub_a_hanoi' | 'hub_b_halong' | None (nằm ngoài mọi vùng phủ).
    """
    conn = get_connection()
    cur = conn.cursor()

    point = "ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography"

    # Check vùng Hà Nội (Hub A)
    cur.execute(f"""
        SELECT ST_DWithin(
            {point},
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s
        );
    """, (lng, lat, *HANOI_CENTER, RADIUS_HANOI_M))
    if cur.fetchone()[0]:
        cur.close()
        conn.close()
        return "hub_a_hanoi"

    # Check vùng Hải Phòng hoặc Hạ Long (Hub B - gộp chung như logic mock data)
    cur.execute(f"""
        SELECT
            ST_DWithin({point}, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, %s)
            OR
            ST_DWithin({point}, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, %s);
    """, (lng, lat, *HAIPHONG_CENTER, RADIUS_DELIVERY_M, *HALONG_CENTER, RADIUS_DELIVERY_M))
    is_hub_b = cur.fetchone()[0]

    cur.close()
    conn.close()
    return "hub_b_halong" if is_hub_b else None


def resolve_order_point(lng: float, lat: float) -> dict:
    """
    Gộp 2 bước trên: từ 1 tọa độ (pickup hoặc delivery), trả về đầy đủ thông tin
    cần lưu vào bảng orders.
    """
    node_id = find_nearest_node(lng, lat)
    hub_zone = classify_hub_zone(lng, lat)

    return {
        "node_id": node_id,
        "hub_zone": hub_zone,
        "valid": node_id is not None and hub_zone is not None,
    }


if __name__ == "__main__":
    # Test nhanh với tọa độ Hồ Gươm vừa geocode được
    result = resolve_order_point(105.8525357, 21.0288313)
    print(result)