-- schema cho do an chuyen tien - phan DB (Nguoi 2 lam them)
-- thiet ke bam sat crypto_utils.py: khong luu du lieu tho, chi luu ket qua da qua ma hoa/ky

PRAGMA foreign_keys = ON;

-- ===== USERS =====
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,          -- ra tu hash_password() - bcrypt, khong bao gio luu plain text
    public_key_pem TEXT NOT NULL,         -- public key cua user, dung de verify chu ky giao dich
    created_at REAL NOT NULL DEFAULT (strftime('%s','now'))
);

-- ===== ACCOUNTS =====
-- khong luu balance dang so nguyen tho -> luu duoi dang AES-GCM ciphertext
-- (ket qua tra ve tu ham aes_encrypt() trong crypto_utils.py)
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    balance_nonce TEXT NOT NULL,          -- enc["nonce"]
    balance_ciphertext TEXT NOT NULL,     -- enc["ciphertext"]
    updated_at REAL NOT NULL DEFAULT (strftime('%s','now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ===== TRANSACTIONS =====
-- luu day du cac field cua payload tu build_transaction_payload()
-- muc dich: lam audit trail - sau nay neu co tranh chap thi con signature/hash de doi chieu lai,
-- giong nhu ngan hang giu log giao dich de tra soat
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,      -- uuid tu generate_transaction_id()
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,              -- luu duoi dang so nguyen (vd: xu/dong), khong dung float
    nonce TEXT NOT NULL,
    timestamp REAL NOT NULL,
    data_hash TEXT NOT NULL,
    signature TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'rejected')),
    reject_reason TEXT,                   -- neu status = rejected thi ghi ly do (vd: "replay attack")
    created_at REAL NOT NULL DEFAULT (strftime('%s','now')),
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);

-- ===== USED_NONCES =====
-- thay the cho NonceTracker luu trong RAM (dict) - phai luu xuong DB de song sot qua lan restart server
-- neu chi luu RAM: hacker doi server restart roi replay lai giao dich cu se lot qua duoc
CREATE TABLE IF NOT EXISTS used_nonces (
    nonce TEXT PRIMARY KEY,
    used_at REAL NOT NULL
);

-- index de tra cuu/purge nonce het han cho nhanh (NonceTracker co max_age_seconds)
CREATE INDEX IF NOT EXISTS idx_used_nonces_used_at ON used_nonces(used_at);
CREATE INDEX IF NOT EXISTS idx_transactions_sender ON transactions(sender_id);
CREATE INDEX IF NOT EXISTS idx_transactions_receiver ON transactions(receiver_id);
