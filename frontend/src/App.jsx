import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import OrderForm from './OrderForm';
import Dashboard from './Dashboard';

function App() {
  return (
    <BrowserRouter>
      <div style={{ padding: 20 }}>
        <h1 style={{ textAlign: 'center' }}>Hệ thống Điều phối Logistics</h1>
        <nav style={{ textAlign: 'center', marginBottom: 20 }}>
          <Link to="/" style={{ marginRight: 16 }}>Nhập đơn</Link>
          <Link to="/dashboard">Quản lý & Bản đồ</Link>
        </nav>
        <Routes>
          <Route path="/" element={<OrderForm />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;