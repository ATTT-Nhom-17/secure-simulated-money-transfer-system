# Security Module — API bàn giao cho Người 1 (Backend)

File: `crypto_utils.py`. Không phụ thuộc gì vào socket/DB — chỉ cần `pip install cryptography bcrypt`.
Mọi giá trị đi qua mạng hoặc lưu JSON đều đã là `str` (PEM hoặc base64), không phải bytes.

## 1. Thiết lập ban đầu (mỗi bên: client, server)

```python
private_pem, public_pem = generate_rsa_keypair()
```
Server và mỗi client tự tạo 1 cặp khóa lúc khởi tạo. Chỉ `public_pem` được gửi qua mạng.
`private_pem` giữ cục bộ (lưu file hoặc biến trong RAM), **không bao giờ truyền đi**.

## 2. Trao đổi khóa phiên (session key) — dùng khi bắt đầu 1 giao dịch

```python
aes_key = generate_aes_key()                              # sinh ở phía gửi
wrapped = rsa_encrypt_key(server_public_pem, aes_key)      # mã hóa bằng public key server
# --- gửi `wrapped` (str) qua socket tới server ---
aes_key = rsa_decrypt_key(server_private_pem, wrapped)     # server giải mã, thu lại aes_key
```

## 3. Tạo và gửi 1 giao dịch (phía client)

```python
payload = build_transaction_payload(sender_id, receiver_id, amount, sender_private_pem)
# payload là dict thuần JSON-serializable, gồm:
#   transaction_id, sender_id, receiver_id, amount, nonce, timestamp, data_hash, signature
json_message = json.dumps(payload)
# --- gửi json_message qua socket (có thể bọc thêm AES nếu muốn ẩn nội dung) ---
```

## 4. Xác minh giao dịch (phía server) — bắt buộc gọi trước khi trừ/cộng tiền

```python
tracker = NonceTracker()   # 1 instance sống suốt vòng đời server, không tạo mới mỗi lần

try:
    verify_transaction_payload(payload, sender_public_pem, tracker)
    # hợp lệ -> tiến hành cập nhật số dư
except TransactionError as e:
    # từ chối giao dịch, log lý do: str(e)
    # các lý do có thể: "invalid signature", "nonce already used (replay attack detected)",
    #                    "data_hash mismatch (payload was tampered with)",
    #                    "timestamp outside allowed window (stale or replayed)"
```

**Quan trọng:** `tracker` phải là **một object dùng chung** cho toàn bộ server (không tạo `NonceTracker()` mới mỗi request), vì nó là bộ nhớ để phát hiện nonce trùng lặp.

## 5. Mã hóa/lưu trữ số dư tài khoản (AES-256-GCM)

```python
key = generate_aes_key()                       # sinh 1 lần, lưu an toàn phía server
enc = aes_encrypt(key, str(balance).encode())  # enc = {"nonce": "...", "ciphertext": "..."}
# lưu enc["nonce"] và enc["ciphertext"] vào accounts.json/DB thay vì số dư thô

balance = int(aes_decrypt(key, enc["nonce"], enc["ciphertext"]).decode())
```
Nếu ai đó sửa `ciphertext` trong file lưu trữ, `aes_decrypt` sẽ raise `cryptography.exceptions.InvalidTag` — bắt exception này để phát hiện dữ liệu bị sửa.

## 6. Mật khẩu đăng nhập

```python
stored_hash = hash_password(raw_password)          # lưu stored_hash vào DB lúc đăng ký
ok = verify_password(raw_password_nhap_vao, stored_hash)   # dùng lúc đăng nhập
```

## 7. Bảng tóm tắt hàm

| Hàm | Vào | Ra | Dùng khi |
|---|---|---|---|
| `generate_rsa_keypair()` | — | `(private_pem, public_pem)` | khởi tạo mỗi bên |
| `rsa_encrypt_key(pub, aes_key)` | public key, bytes | base64 str | gửi session key |
| `rsa_decrypt_key(priv, wrapped)` | private key, base64 str | bytes | nhận session key |
| `build_transaction_payload(...)` | id, id, số tiền, private key | dict | client tạo giao dịch |
| `verify_transaction_payload(...)` | dict, public key, tracker | raise hoặc None | server xác minh |
| `aes_encrypt(key, plaintext)` | bytes, bytes | dict {nonce, ciphertext} | mã hóa số dư |
| `aes_decrypt(key, nonce, ct)` | bytes, str, str | bytes | giải mã số dư |
| `hash_password(pw)` | str | str | lúc đăng ký |
| `verify_password(pw, hash)` | str, str | bool | lúc đăng nhập |

## 8. Test / demo

`python3 test_crypto_utils.py` — chạy toàn bộ self-test, bao gồm 3 kịch bản tấn công giả lập
(sửa gói tin, replay attack, timestamp cũ) để dùng làm bằng chứng trong báo cáo/bảo vệ đồ án.
