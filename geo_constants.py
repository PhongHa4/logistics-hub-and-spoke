# Các hằng số địa lý dùng chung toàn dự án - tránh lặp lại ở nhiều file

# --- Cấu hình 3 Hub (tổng quát, dễ thêm/bớt Hub sau này) ---
HUBS = {
    "hub_a_hanoi": {
        "center": (105.8542, 21.0285),
        "radius_m": 15000,
        "node_id": 1019649,
    },
    "hub_b_haiphong": {
        "center": (106.6881, 20.8449),
        "radius_m": 10000,
        "node_id": 54518,
    },
    "hub_c_halong": {
        "center": (107.0797, 20.9515),
        "radius_m": 10000,
        "node_id": 501759,
    },
}

# Ngưỡng chấp nhận khi tìm node gần nhất từ tọa độ geocode (mét)
NEAREST_NODE_RADIUS_M = 2000