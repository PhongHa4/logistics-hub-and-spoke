from db import get_connection   # thay vì "from main import get_connection"
from geo_constants import HUBS, NEAREST_NODE_RADIUS_M


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
    Xác định 1 điểm tọa độ thuộc vùng phủ của Hub nào trong số các Hub cấu hình ở HUBS.
    Trả về key của Hub (vd 'hub_a_hanoi') hoặc None nếu ngoài mọi vùng phủ.
    """
    conn = get_connection()
    cur = conn.cursor()

    for hub_key, hub_info in HUBS.items():
        center_lng, center_lat = hub_info["center"]
        cur.execute("""
            SELECT ST_DWithin(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            );
        """, (lng, lat, center_lng, center_lat, hub_info["radius_m"]))
        if cur.fetchone()[0]:
            cur.close()
            conn.close()
            return hub_key

    cur.close()
    conn.close()
    return None


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