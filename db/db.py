import os
import sqlite3
import time

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "transfer_system.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # de query tra ve duoc nhu dict, de xai hon tuple
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=DB_PATH, schema_path=SCHEMA_PATH):
    conn = get_connection(db_path)
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


# ===== USERS =====

def create_user(conn, username, password_hash, public_key_pem, pin_hash=None, private_key_pem=None):
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, pin_hash, public_key_pem, private_key_pem) VALUES (?, ?, ?, ?, ?)",
        (username, password_hash, pin_hash, public_key_pem, private_key_pem),
    )
    conn.commit()
    return cur.lastrowid


def get_user_by_username(conn, username):
    return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user_by_id(conn, user_id):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


# ===== ACCOUNTS =====
# balance luon luu duoi dang nonce+ciphertext (dau ra cua aes_encrypt), khong bao gio luu so tho

def create_account(conn, user_id, balance_nonce, balance_ciphertext):
    conn.execute(
        "INSERT INTO accounts (user_id, balance_nonce, balance_ciphertext) VALUES (?, ?, ?)",
        (user_id, balance_nonce, balance_ciphertext),
    )
    conn.commit()


def get_account(conn, user_id):
    return conn.execute("SELECT * FROM accounts WHERE user_id = ?", (user_id,)).fetchone()


def update_balance(conn, user_id, balance_nonce, balance_ciphertext):
    conn.execute(
        "UPDATE accounts SET balance_nonce = ?, balance_ciphertext = ?, updated_at = ? WHERE user_id = ?",
        (balance_nonce, balance_ciphertext, time.time(), user_id),
    )
    conn.commit()


# ===== TRANSACTIONS =====

def insert_transaction(conn, payload, status="pending", reject_reason=None, description=None):
    # payload la dict tra ve tu build_transaction_payload() ben crypto_utils.py
    conn.execute(
        """INSERT INTO transactions
           (transaction_id, sender_id, receiver_id, amount, description, nonce, timestamp, data_hash, signature, status, reject_reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            payload["transaction_id"], payload["sender_id"], payload["receiver_id"], payload["amount"],
            description or payload.get("description"),
            payload["nonce"], payload["timestamp"], payload["data_hash"], payload["signature"],
            status, reject_reason,
        ),
    )
    conn.commit()


def update_transaction_status(conn, transaction_id, status, reject_reason=None):
    conn.execute(
        "UPDATE transactions SET status = ?, reject_reason = ? WHERE transaction_id = ?",
        (status, reject_reason, transaction_id),
    )
    conn.commit()


def get_transactions_for_user(conn, user_id):
    return conn.execute(
        """SELECT t.*, u1.username AS sender_username, u2.username AS receiver_username
           FROM transactions t
           JOIN users u1 ON t.sender_id = u1.id
           JOIN users u2 ON t.receiver_id = u2.id
           WHERE t.sender_id = ? OR t.receiver_id = ?
           ORDER BY t.created_at DESC""",
        (user_id, user_id),
    ).fetchall()


def get_transaction_by_id(conn, transaction_id):
    return conn.execute(
        """SELECT t.*, u1.username AS sender_username, u2.username AS receiver_username,
                  u1.public_key_pem AS sender_public_key_pem
           FROM transactions t
           JOIN users u1 ON t.sender_id = u1.id
           JOIN users u2 ON t.receiver_id = u2.id
           WHERE t.transaction_id = ?""",
        (transaction_id,),
    ).fetchone()


# ===== NONCE TRACKER BAN DB =====
# cung interface (seen / mark_used) nhu NonceTracker trong crypto_utils.py de Nguoi 1
# co the doi qua ban nay ma khong phai sua verify_transaction_payload()

class DBNonceTracker:
    def __init__(self, conn, max_age_seconds=300):
        self.conn = conn
        self.max_age_seconds = max_age_seconds

    def _purge_expired(self, now):
        self.conn.execute(
            "DELETE FROM used_nonces WHERE ? - used_at > ?", (now, self.max_age_seconds)
        )
        self.conn.commit()

    def seen(self, nonce):
        row = self.conn.execute("SELECT 1 FROM used_nonces WHERE nonce = ?", (nonce,)).fetchone()
        return row is not None

    def mark_used(self, nonce, timestamp):
        self._purge_expired(timestamp)
        self.conn.execute(
            "INSERT OR IGNORE INTO used_nonces (nonce, used_at) VALUES (?, ?)", (nonce, timestamp)
        )
        self.conn.commit()


if __name__ == "__main__":
    # test nhanh: tao db, tao 1 user, tao 1 account
    init_db()
    conn = get_connection()
    uid = create_user(conn, "test_user", "fake_hash", "fake_pem", "fake_pin_hash", "fake_priv_pem")
    create_account(conn, uid, "fake_nonce", "fake_ciphertext")
    print("da tao user id:", uid)
    print(dict(get_account(conn, uid)))
    conn.close()
