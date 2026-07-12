import json
from db import get_connection


def get_route_geometry(node_sequence: list[int]) -> dict | None:
    """
    Lấy geometry GeoJSON (LineString) thực tế đi qua các node liên tiếp trong node_sequence.
    Ghép nối từng chặng (mỗi cặp node liền kề) lại thành 1 đường duy nhất.
    """
    conn = get_connection()
    cur = conn.cursor()

    all_edges = []
    for i in range(len(node_sequence) - 1):
        src, dst = node_sequence[i], node_sequence[i + 1]
        if src == dst:
            continue  # bỏ qua chặng trùng điểm (VD 2 đơn cùng địa chỉ)
        cur.execute("""
            SELECT edge FROM pgr_dijkstra(
                'SELECT id, source, target, cost_s AS cost, reverse_cost_s AS reverse_cost FROM ways',
                %s, %s, directed := true
            ) WHERE edge != -1;
        """, (src, dst))
        all_edges.extend(row[0] for row in cur.fetchall())

    if not all_edges:
        cur.close()
        conn.close()
        return None

    cur.execute("""
        SELECT ST_AsGeoJSON(
            ST_LineMerge(ST_Collect(geom ORDER BY array_position(%s::bigint[], id)))
        )
        FROM ways WHERE id = ANY(%s::bigint[]);
    """, (all_edges, all_edges))

    geojson_str = cur.fetchone()[0]
    cur.close()
    conn.close()
    return json.loads(geojson_str) if geojson_str else None


if __name__ == "__main__":
    # Test với route First-mile thật vừa chạy được ở bước trước
    result = get_route_geometry([1019649, 472494, 1019649])
    print(json.dumps(result, indent=2))