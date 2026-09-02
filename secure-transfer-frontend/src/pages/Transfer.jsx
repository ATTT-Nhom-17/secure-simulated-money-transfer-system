import React from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { transfer } from "../services/api";

export default function Transfer() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    receiver: "",
    amount: "",
    description: "",
    pin: "",
  });
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    if (!/^\d{6}$/.test(form.pin)) {
      setError("Enter your 6-digit transfer PIN.");
      return;
    }
    setLoading(true);
    try {
      const res = await transfer({ ...form, amount: Number(form.amount) });
      setResult(res);
      setForm({ receiver: "", amount: "", description: "", pin: "" });
    } catch (err) {
      setError(err.message || "Transfer failed.");
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="page narrow">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Chuyển tiền</p>
          <h1>Chuyển tiền</h1>
          <p className="muted">
            Create a transaction that will be verified by the backend security
            layer.
          </p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {result && (
        <div className="alert success">
          <strong>✓ Chuyển tiền thành công.</strong> Transaction ID:{" "}
          <span className="mono">{result.transaction_id}</span>
          <button
            className="inline-link"
            onClick={() => navigate(`/transactions/${result.transaction_id}`)}
          >
            Xem chi tiết
          </button>
        </div>
      )}
      <section className="panel">
        <form onSubmit={submit} className="form-stack">
          <label>
            Receiver
            <input
              required
              placeholder="e.g. user2"
              value={form.receiver}
              onChange={(e) => setForm({ ...form, receiver: e.target.value })}
            />
          </label>
          <label>
            Amount (VND)
            <input
              required
              type="number"
              min="1"
              placeholder="500000"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
            />
          </label>
          <label>
            Description
            <textarea
              rows="4"
              placeholder="Transfer for demo"
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
            />
          </label>
          <label>
            Transfer PIN
            <input
              required
              type="password"
              inputMode="numeric"
              autoComplete="off"
              maxLength="6"
              pattern="[0-9]{6}"
              placeholder="6-digit PIN"
              value={form.pin}
              onChange={(e) =>
                setForm({
                  ...form,
                  pin: e.target.value.replace(/\D/g, "").slice(0, 6),
                })
              }
            />
          </label>
          <div className="security-preview">
            <div>
              <strong>Security checks</strong>
              <span>SHA-256 hash → RSA signature → replay protection</span>
            </div>
            <span className="pill">SECURE</span>
          </div>
          <button className="btn btn-primary" disabled={loading}>
            {loading ? "Processing..." : "Confirm Transfer"}
          </button>
        </form>
      </section>
    </div>
  );
}

