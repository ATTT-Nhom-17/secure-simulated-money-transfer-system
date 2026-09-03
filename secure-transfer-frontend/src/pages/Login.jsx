import React from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../services/api";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "user1", password: "123456" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="logo-big">$</div>
        <h1>Secure Transfer</h1>
        <p className="muted">Sign in to your secure demo account</p>
        {error && <div className="alert error">{error}</div>}
        <form onSubmit={submit} className="form-stack">
          <label>
            Username
            <input
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </label>
          <button className="btn btn-primary full" disabled={loading}>
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>
        <div className="demo-note">
          Demo account: <strong>user1</strong> / <strong>123456</strong>
        </div>
        <p className="auth-switch">
          Chưa có tài khoản? <Link to="/register">Đăng ký</Link>
        </p>
      </div>
    </div>
  );
}
