import React from "react";
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';
import { getTransaction } from '../services/api';

export default function TransactionDetail() {
  const { id } = useParams(); const [tx, setTx] = useState(null); const [error, setError] = useState('');
  useEffect(() => { getTransaction(id).then(setTx).catch(e => setError(e.message)); }, [id]);
  if (error) return <div className="page"><div className="alert error">{error}</div><Link className="link" to="/transactions">← Back to history</Link></div>;
  if (!tx) return <div className="page"><div className="loading">Loading transaction...</div></div>;
  return <div className="page narrow"><div className="page-heading"><div><p className="eyebrow">Transaction Detail</p><h1 className="mono">{tx.transaction_id}</h1></div><Link className="btn btn-ghost" to="/transactions">← Back</Link></div>
    <section className="panel detail-grid">
      <div><span>Sender</span><strong>{tx.sender}</strong></div><div><span>Receiver</span><strong>{tx.receiver}</strong></div><div><span>Amount</span><strong>{Number(tx.amount).toLocaleString('vi-VN')} VND</strong></div><div><span>Status</span><strong><StatusBadge status={tx.status} /></strong></div><div><span>Timestamp</span><strong>{(() => {
        if (!tx.timestamp) return "—";
        const num = Number(tx.timestamp);
        const date = !isNaN(num) ? new Date(num > 1e11 ? num : num * 1000) : new Date(tx.timestamp);
        return isNaN(date.getTime()) ? String(tx.timestamp) : date.toLocaleString("vi-VN");
      })()}</strong></div><div><span>Nonce</span><strong className="mono small-text">{tx.nonce || '—'}</strong></div>
    </section>
    <section className="panel"><div className="panel-head"><h2>Security Verification</h2></div><div className="verification-list">
      <div className="verify-row"><div><strong>SHA-256 Hash</strong><small>{tx.hash || 'Not available'}</small></div><span className={tx.hash_valid ? 'check good' : 'check bad'}>{tx.hash_valid ? 'VALID ✓' : 'INVALID ✗'}</span></div>
      <div className="verify-row"><div><strong>RSA Digital Signature</strong><small>{tx.signature || 'Not available'}</small></div><span className={tx.signature_valid ? 'check good' : 'check bad'}>{tx.signature_valid ? 'VERIFIED ✓' : 'FAILED ✗'}</span></div>
      <div className="verify-row"><div><strong>Replay Protection</strong><small>transaction_id + nonce + timestamp</small></div><span className={tx.replay_detected ? 'check bad' : 'check good'}>{tx.replay_detected ? 'BLOCKED' : 'PASSED ✓'}</span></div>
    </div></section>
  </div>;
}
