import React from "react";
import { useEffect, useState } from "react";
import TransactionTable from "../components/TransactionTable";
import { getTransactions } from "../services/api";

export default function Transactions() {
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    getTransactions()
      .then((r) => setTxs(r.transactions || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Lịch sử</p>
          <h1>Lịch sử giao dịch</h1>
          <p className="muted">
            Xem lại các lần chuyển tiền thành công và bị chặn.
          </p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      <section className="panel">
        {loading ? (
          <div className="loading">Đang tải giao dịch...</div>
        ) : (
          <TransactionTable transactions={txs} />
        )}
      </section>
    </div>
  );
}
