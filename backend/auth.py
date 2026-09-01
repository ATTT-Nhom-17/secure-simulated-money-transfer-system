import os
import sys

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

# tro toi 2 thu muc db/ va security/ de import duoc db.py va crypto_utils.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "db"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "security"))
import db
import crypto_utils as cu
from database import get_db
from config import SERVER_BALANCE_KEY
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from security import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register", response_model=UserResponse)
def register(req: RegisterRequest, conn=Depends(get_db)):
    if db.get_user_by_username(conn, req.username):
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    if len(req.pin) != 6 or not req.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN phải là 6 chữ số")

    # moi user co 1 cap khoa RSA rieng, dung de ky/verify giao dich cua chinh ho
    private_pem, public_pem = cu.generate_rsa_keypair()

    user_id = db.create_user(
        conn,
        username=req.username,
        password_hash=cu.hash_password(req.password),
        pin_hash=cu.hash_password(req.pin),  # dung chung ham hash_password, ban chat van la bcrypt 1 chieu
        public_key_pem=public_pem,
        private_key_pem=private_pem,
    )

    # Khoi tao so du ban dau (10,000,000 VND) phuc vu demo chuyen tien
    initial_balance = 10_000_000
    enc = cu.aes_encrypt(SERVER_BALANCE_KEY, str(initial_balance).encode())
    db.create_account(conn, user_id, enc["nonce"], enc["ciphertext"])

    return UserResponse(id=user_id, username=req.username, email=req.email, balance=initial_balance)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, conn=Depends(get_db)):
    user = db.get_user_by_username(conn, req.username)
    if not user or not cu.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Sai username hoặc password")

    token = create_access_token({"sub": str(user["id"])})
    return TokenResponse(access_token=token, username=user["username"])


def get_current_user(token: str = Depends(oauth2_scheme), conn=Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc hết hạn")

    user = db.get_user_by_id(conn, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User không tồn tại")
    return user


def get_user_balance(conn, user_id: int) -> int:
    account = db.get_account(conn, user_id)
    if not account:
        initial_balance = 10_000_000
        enc = cu.aes_encrypt(SERVER_BALANCE_KEY, str(initial_balance).encode())
        db.create_account(conn, user_id, enc["nonce"], enc["ciphertext"])
        return initial_balance
    try:
        return int(cu.aes_decrypt(SERVER_BALANCE_KEY, account["balance_nonce"], account["balance_ciphertext"]).decode())
    except Exception:
        # Neu key cu khong khop sau khi restart, reset ve so du demo 10,000,000 VND voi key moi
        initial_balance = 10_000_000
        enc = cu.aes_encrypt(SERVER_BALANCE_KEY, str(initial_balance).encode())
        db.update_balance(conn, user_id, enc["nonce"], enc["ciphertext"])
        return initial_balance


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user), conn=Depends(get_db)):
    balance = get_user_balance(conn, current_user["id"])
    return UserResponse(id=current_user["id"], username=current_user["username"], balance=balance)
