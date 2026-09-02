import React from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Transfer from "./pages/Transfer";
import Transactions from "./pages/Transactions";
import TransactionDetail from "./pages/TransactionDetail";

function Layout({ children }) {
  const location = useLocation();

  const isAuthPage =
    location.pathname === "/login" || location.pathname === "/register";

  return (
    <div className="app-shell">
      {!isAuthPage && <Navbar />}

      <main className={isAuthPage ? "auth-main" : "main-content"}>
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <Layout>
      <Routes>
        {/* Trang mặc định */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Authentication */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected pages */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />

          <Route path="/transfer" element={<Transfer />} />

          <Route path="/transactions" element={<Transactions />} />

          <Route path="/transactions/:id" element={<TransactionDetail />} />
        </Route>

        {/* Không tìm thấy trang */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
