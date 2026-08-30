import React from "react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import BalanceCard from "../components/BalanceCard";
import TransactionTable from "../components/TransactionTable";
import { getAccount, getBalance, getTransactions } from "../services/api";

export default function Dashboard() {
  const [account, setAccount] = useState(null);
  const [balance, setBalance] = useState(0);
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => {
    try {
      setLoading(true);
      const [a, b, t] = await Promise.all([
        getAccount(),
        getBalance(),
        getTransactions(),
      ]);
      setAccount(a);
      setBalance(b.balance);
      setTxs((t.transactions || []).slice(0, 5));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Trang chủ</p>
          <h1>Chào mừng, {account?.username || "User"} 👋</h1>
        </div>
        <Link className="btn btn-primary" to="/transfer">
          Chuyển tiền & Thanh toán
        </Link>
      </div>
      {error && <div className="alert error">{error}</div>}
      {loading ? (
        <div className="loading">Đang tải tài khoản...</div>
      ) : (
        <>
          <BalanceCard balance={balance} />
          <div className="security-grid">
            <div className="security-card">
              <span>RSA</span>
              <div>
                <strong>Chữ ký số</strong>
                <small>Xác minh tính xác thực của giao dịch</small>
              </div>
              <b>✓</b>
            </div>
            <div className="security-card">
              <span>AES</span>
              <div>
                <strong>Mã hóa cân bằng</strong>
                <small>AES-256-GCM protection</small>
              </div>
              <b>✓</b>
            </div>
            <div className="security-card">
              <span>24/7</span>
              <div>
                <strong>Bảo vệ phát lại</strong>
                <small>Nonce + dấu thời gian đã được kiểm tra</small>
              </div>
              <b>✓</b>
            </div>
          </div>
          <section className="panel">
            <div className="panel-head">
              <h2>Giao dịch gần đây</h2>
              <Link className="link" to="/transactions">
                Kiểm tra tất cả
              </Link>
            </div>
            <TransactionTable transactions={txs} />
          </section>
        </>
      )}
    </div>
  );
}
