import os
import sys

# repo chia thanh nhieu thu muc rieng (backend/, db/, security/), nen phai tro dan
# toi thu muc security/ moi import duoc crypto_utils.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "security"))
import crypto_utils as cu

# JWT secret - demo thoi, deploy that phai doc tu .env
JWT_SECRET = "day-la-secret-key-demo-doan-nay-nho-doi-khi-deploy"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

# key dung de ma hoa balance cua TAT CA account (AES-256-GCM)
# tradeoff: thuc te phai luu trong KMS/HSM (vd AWS KMS), o day de don gian nen
# luu ra 1 file local - chi de balance con doc lai duoc sau khi restart server luc demo,
# KHONG dung cach nay khi deploy that (file nay ma bi lo la lo het balance cua toan bo user)
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_KEY_FILE = os.path.join(_CONFIG_DIR, "balance.key")

if os.path.exists(_KEY_FILE):
    with open(_KEY_FILE, "rb") as f:
        SERVER_BALANCE_KEY = f.read()
else:
    SERVER_BALANCE_KEY = cu.generate_aes_key()
    with open(_KEY_FILE, "wb") as f:
        f.write(SERVER_BALANCE_KEY)

