# Các hằng số địa lý dùng chung toàn dự án - tránh lặp lại ở nhiều file

# Tọa độ tâm khu vực (lng, lat)
HANOI_CENTER = (105.8542, 21.0285)
HAIPHONG_CENTER = (106.6881, 20.8449)
HALONG_CENTER = (107.0797, 20.9515)

# Bán kính vùng phủ mỗi Hub (mét)
RADIUS_HANOI_M = 15000
RADIUS_DELIVERY_M = 10000

# Node id của 2 Hub trên mạng lưới pgRouting (dùng cho VRP)
HUB_A_HANOI_NODE = 1019649
HUB_B_HALONG_NODE = 501759

# Ngưỡng chấp nhận khi tìm node gần nhất từ tọa độ geocode (mét)
NEAREST_NODE_RADIUS_M = 2000