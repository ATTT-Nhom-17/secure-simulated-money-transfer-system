import React from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../services/api";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    if (form.password !== form.confirmPassword)
      return setError("Passwords do not match.");
    setLoading(true);
    try {
      const res = await register(form);
      setMessage(res.message || "Registration successful");
      setTimeout(() => navigate("/login"), 900);
    } catch (err) {
      setError(err.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="logo-big">$</div>
        <h1>Create Account</h1>
        <p className="muted">Register a demo secure-transfer account</p>
        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}
        <form onSubmit={submit} className="form-stack">
          <label>
            Username
            <input
              required
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </label>
          <label>
            Email
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </label>
          <label>
            Confirm Password
            <input
              type="password"
              required
              value={form.confirmPassword}
              onChange={(e) =>
                setForm({ ...form, confirmPassword: e.target.value })
              }
            />
          </label>
          <button className="btn btn-primary full" disabled={loading}>
            {loading ? "Creating..." : "Create Account"}
          </button>
        </form>
        <p className="auth-switch">
          Đã có tài khoản chưa? <Link to="/login">Đăng nhập</Link>
        </p>
      </div>
    </div>
  );
}
