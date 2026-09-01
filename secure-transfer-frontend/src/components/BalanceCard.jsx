import React from "react";
export default function BalanceCard({ balance }) {
  return (
    <section className="balance-card">
      <div>
        <p className="eyebrow">Số Dư Hiện Tại</p>
        <h2>
          {Number(balance || 0).toLocaleString("vi-VN")} <span>VND</span>
        </h2>
        <p className="muted">Protected in database with AES-256-GCM.</p>
      </div>
      <div className="shield">✓</div>
    </section>
  );
}
