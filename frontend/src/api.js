const API_BASE = 'http://localhost:8000';

export async function createOrder(order) {
  const res = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(order),
  });
  if (!res.ok) throw new Error('Tạo đơn thất bại');
  return res.json();
}

export async function listOrders(status) {
  const url = status ? `${API_BASE}/orders?status=${status}` : `${API_BASE}/orders`;
  const res = await fetch(url);
  return res.json();
}

export async function calculateRoutes() {
  const res = await fetch(`${API_BASE}/calculate-routes`, { method: 'POST' });
  return res.json();
}

export async function getLatestRoutes() {
  const res = await fetch(`${API_BASE}/routes/latest`);
  return res.json();
}