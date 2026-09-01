import React from "react";
import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge";

export default function TransactionTable({ transactions = [] }) {
  if (!transactions.length)
    return <div className="empty-state">Chưa có giao dịch nào.</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Người nhận</th>
            <th>Số lượng</th>
            <th>Thời gian</th>
            <th>Trạng thái</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx) => (
            <tr key={tx.transaction_id}>
              <td className="mono">{tx.transaction_id}</td>
              <td>{tx.receiver}</td>
              <td>{Number(tx.amount).toLocaleString("vi-VN")} VND</td>
              <td>
                {(() => {
                  if (!tx.timestamp) return "—";
                  const num = Number(tx.timestamp);
                  const date = !isNaN(num)
                    ? new Date(num > 1e11 ? num : num * 1000)
                    : new Date(tx.timestamp);
                  return isNaN(date.getTime()) ? String(tx.timestamp) : date.toLocaleString("vi-VN");
                })()}
              </td>
              <td>
                <StatusBadge status={tx.status} />
              </td>
              <td>
                <Link
                  className="link"
                  to={`/transactions/${tx.transaction_id}`}
                >
                  Details →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
