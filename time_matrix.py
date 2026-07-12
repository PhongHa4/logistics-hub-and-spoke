from db import get_connection


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