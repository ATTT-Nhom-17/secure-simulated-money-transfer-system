# Demo script - Người 3

## Demo 1: Normal transfer

1. Login with `user1 / 123456`.
2. Show current balance.
3. Open Transfer.
4. Enter transfer PIN `123456` and send `500000 VND` to `user2`.
5. Show `SUCCESS` and the generated transaction ID.
6. Open Transaction Detail.
7. Show SHA-256, RSA signature, nonce/timestamp, and replay-protection status.

## Demo 2: Tamper with transaction data

Use a captured API request in an API client during the real-backend demo.

1. Create a valid request with amount `500000`.
2. Change the amount to `5000000` without re-signing.
3. Send the modified request.
4. Expected backend result: signature verification fails and the transfer is rejected.
5. Show the failed transaction/security message in the UI.

## Demo 3: Replay attack

1. Capture one valid transfer request.
2. Send the exact same request again with the same transaction_id/nonce/timestamp.
3. Expected backend result: replay attack is detected and the request is rejected.
4. Show `Replay detected / blocked` on the transaction detail or API response.

## What to say

“Em phụ trách Frontend, Testing và Demo. Frontend cung cấp các màn hình đăng ký, đăng nhập, dashboard, chuyển tiền, lịch sử và chi tiết giao dịch. Khi ghép với backend, giao diện hiển thị trạng thái xác minh SHA-256, chữ ký RSA và cơ chế chống replay. Trong demo, em thực hiện một giao dịch bình thường, sau đó mô phỏng sửa số tiền và gửi lại request cũ để chứng minh hệ thống từ chối các giao dịch không hợp lệ.”
