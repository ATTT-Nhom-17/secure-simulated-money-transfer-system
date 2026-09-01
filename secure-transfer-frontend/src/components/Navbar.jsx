import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { logout } from "../services/api";

export default function Navbar() {
  const navigate = useNavigate();
  const user = JSON.parse(
    localStorage.getItem("user") || '{"username":"user1"}',
  );
  const handleLogout = () => {
    logout();
    navigate("/login");
  };
  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand-mark">$</span> HHHBank
      </div>
      <nav className="nav-links">
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/transfer">Transfer</NavLink>
        <NavLink to="/transactions">Lịch sử</NavLink>
      </nav>
      <div className="topbar-right">
        <span className="user-chip">{user.username}</span>
        <button className="btn btn-ghost" onClick={handleLogout}>
          Đăng xuất
        </button>
      </div>
    </header>
  );
}
