import { useState, useEffect } from 'react';
import { listOrders, calculateRoutes } from './api';
import MapView from './MapView';

export default function Dashboard() {
  const [orders, setOrders] = useState([]);
  const [calculating, setCalculating] = useState(false);
  const [mapKey, setMapKey] = useState(0); // dùng để ép MapView render lại sau khi tính toán xong

  const loadOrders = async () => {
    const data = await listOrders();
    setOrders(data);
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleCalculate = async () => {
    setCalculating(true);
    try {
      const result = await calculateRoutes();
      alert(`${result.message} (batch_id: ${result.batch_id ?? 'N/A'})`);
      await loadOrders();
      setMapKey((k) => k + 1); // ép MapView tải lại route mới
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div>
      <h2>Quản lý đơn hàng</h2>
      <button onClick={handleCalculate} disabled={calculating}>
        {calculating ? 'Đang tính toán (có thể mất 20-30s)...' : 'Bắt đầu tính toán tuyến đường'}
      </button>

      <table border="1" cellPadding="6" style={{ marginTop: 16, width: '100%' }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Lấy hàng</th>
            <th>Giao hàng</th>
            <th>KL (kg)</th>
            <th>Trạng thái</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td>{o.id}</td>
              <td>{o.pickup_address}</td>
              <td>{o.delivery_address}</td>
              <td>{o.demand_kg}</td>
              <td>{o.status}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 style={{ marginTop: 30 }}>Bản đồ tuyến đường (batch gần nhất)</h2>
      <MapView key={mapKey} />
    </div>
  );
}