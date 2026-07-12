import { useState } from 'react';
import { createOrder } from './api';

export default function OrderForm() {
  const [form, setForm] = useState({ pickup_address: '', delivery_address: '', demand_kg: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const data = await createOrder({
        ...form,
        demand_kg: parseFloat(form.demand_kg),
      });
      setResult(data);
      setForm({ pickup_address: '', delivery_address: '', demand_kg: '' });
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: '0 auto' }}>
      <h2>Nhập đơn hàng</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Địa chỉ lấy hàng:</label>
          <input
            name="pickup_address"
            value={form.pickup_address}
            onChange={handleChange}
            required
            style={{ width: '100%' }}
          />
        </div>
        <div>
          <label>Địa chỉ giao hàng:</label>
          <input
            name="delivery_address"
            value={form.delivery_address}
            onChange={handleChange}
            required
            style={{ width: '100%' }}
          />
        </div>
        <div>
          <label>Khối lượng (kg):</label>
          <input
            name="demand_kg"
            type="number"
            value={form.demand_kg}
            onChange={handleChange}
            required
            style={{ width: '100%' }}
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Đang xử lý...' : 'Tạo đơn'}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: 20 }}>
          {result.error ? (
            <p style={{ color: 'red' }}>Lỗi: {result.error}</p>
          ) : (
            <p>
              Tạo đơn thành công! ID: {result.id}, trạng thái: <b>{result.status}</b>
              {result.status === 'geocode_failed' && (
                <span style={{ color: 'orange' }}> — địa chỉ không xác định được, thử nhập cụ thể hơn</span>
              )}
            </p>
          )}
        </div>
      )}
    </div>
  );
}