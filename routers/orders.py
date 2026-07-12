from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_connection   # thay vì "from main import get_connection"
from geocode import geocode_address
from orders_service import find_nearest_node, classify_hub_zone

router = APIRouter()


class OrderCreate(BaseModel):
    pickup_address: str
    delivery_address: str
    demand_kg: float


@router.post("/orders")
async def create_order(order: OrderCreate):
    # --- Geocode 2 đầu ---
    pickup_geo = await geocode_address(order.pickup_address)
    if pickup_geo is None:
        raise HTTPException(status_code=400, detail="Không tìm thấy địa chỉ lấy hàng")

    delivery_geo = await geocode_address(order.delivery_address)
    if delivery_geo is None:
        raise HTTPException(status_code=400, detail="Không tìm thấy địa chỉ giao hàng")

    # --- Tìm node gần nhất + phân loại hub cho từng đầu ---
    pickup_node = find_nearest_node(pickup_geo["lng"], pickup_geo["lat"])
    pickup_hub = classify_hub_zone(pickup_geo["lng"], pickup_geo["lat"])

    delivery_node = find_nearest_node(delivery_geo["lng"], delivery_geo["lat"])
    delivery_hub = classify_hub_zone(delivery_geo["lng"], delivery_geo["lat"])

    # --- Xác định trạng thái ---
    if None in (pickup_node, pickup_hub, delivery_node, delivery_hub):
        status = "geocode_failed"
    else:
        status = "pending"

    # --- Lưu vào DB ---
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (
            pickup_address, delivery_address,
            pickup_lng, pickup_lat, delivery_lng, delivery_lat,
            pickup_node_id, delivery_node_id,
            pickup_hub_zone, delivery_hub_zone,
            demand_kg, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        order.pickup_address, order.delivery_address,
        pickup_geo["lng"], pickup_geo["lat"], delivery_geo["lng"], delivery_geo["lat"],
        pickup_node, delivery_node,
        pickup_hub, delivery_hub,
        order.demand_kg, status
    ))
    order_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {"id": order_id, "status": status}


@router.get("/orders")
def list_orders(status: str | None = None):
    """List đơn hàng, lọc theo status nếu có truyền vào (?status=pending)"""
    conn = get_connection()
    cur = conn.cursor()

    if status:
        cur.execute("SELECT * FROM orders WHERE status = %s ORDER BY created_at DESC;", (status,))
    else:
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC;")

    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()
    return rows