import React from "react";
export default function StatusBadge({ status }) {
  const cls = String(status).toLowerCase();
  return <span className={`status-badge ${cls}`}>{status}</span>;
}
