import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from security.crypto_utils import (
    generate_rsa_keypair, hash_password, generate_aes_key, aes_encrypt,
    build_transaction_payload, verify_transaction_payload, TransactionError,
)
from db.db import (
    init_db, get_connection, create_user, create_account, get_account,
    insert_transaction, update_transaction_status, DBNonceTracker,
)

DB_FILE = "demo.db"  # rieng cho demo, khong dung chung ten voi DB that cua backend (transfer_system.db)


def main():
    if not os.path.exists(DB_FILE):
        init_db(db_path=DB_FILE, schema_path="db/schema.sql")
        print("da tao file db moi:", DB_FILE)

    conn = get_connection(DB_FILE)

    # ===== tao 2 user: A gui, B nhan =====
    priv_a, pub_a = generate_rsa_keypair()
    priv_b, pub_b = generate_rsa_keypair()

    uid_a = create_user(conn, "user_a", hash_password("MatKhauA123!"), pub_a)
    uid_b = create_user(conn, "user_b", hash_password("MatKhauB123!"), pub_b)
    print(f"da tao user_a (id={uid_a}), user_b (id={uid_b})")

    # ===== tao account voi so du ban dau da ma hoa AES =====
    aes_key = generate_aes_key()  # trong thuc te: moi account 1 key rieng, luu key an toan
    enc_a = aes_encrypt(aes_key, str(1000000).encode())
    enc_b = aes_encrypt(aes_key, str(500000).encode())
    create_account(conn, uid_a, enc_a["nonce"], enc_a["ciphertext"])
    create_account(conn, uid_b, enc_b["nonce"], enc_b["ciphertext"])
    print("da tao account, so du da ma hoa (khong luu so tho)")

    # ===== A chuyen 200000 cho B =====
    payload = build_transaction_payload(sender_id=uid_a, receiver_id=uid_b,
                                         amount=200000, sender_private_key_pem=priv_a)

    tracker = DBNonceTracker(conn)
    try:
        verify_transaction_payload(payload, pub_a, tracker)
        insert_transaction(conn, payload, status="success")
        print("giao dich hop le, da luu vao DB voi status=success")
    except TransactionError as e:
        insert_transaction(conn, payload, status="rejected", reject_reason=str(e))
        print("giao dich bi tu choi:", e)

    conn.close()
    print("\n(day la du lieu demo, khong phai du lieu that cua he thong)")
    print("Mo file", DB_FILE, "bang DB Browser for SQLite de xem ket qua trong cac bang:")
    print("  - users: 2 dong (user_a, user_b) voi password_hash va public_key_pem that")
    print("  - accounts: so du duoi dang nonce + ciphertext, khong phai so tho")
    print("  - transactions: 1 giao dich voi day du signature, data_hash, status=success")
    print("  - used_nonces: 1 dong - nonce cua giao dich vua roi da bi 'dung 1 lan'")


if __name__ == "__main__":
    main()
