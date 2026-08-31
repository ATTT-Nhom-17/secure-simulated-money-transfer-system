from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

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

    # balance khoi tao = 0, ma hoa truoc khi luu, khong bao gio luu so tho
    enc = cu.aes_encrypt(SERVER_BALANCE_KEY, str(0).encode())
    db.create_account(conn, user_id, enc["nonce"], enc["ciphertext"])

    return UserResponse(id=user_id, username=req.username, balance=0)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, conn=Depends(get_db)):
    user = db.get_user_by_username(conn, req.username)
    if not user or not cu.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Sai username hoặc password")

    token = create_access_token({"sub": str(user["id"])})
    return TokenResponse(access_token=token)


def get_current_user(token: str = Depends(oauth2_scheme), conn=Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc hết hạn")

    user = db.get_user_by_id(conn, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User không tồn tại")
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user), conn=Depends(get_db)):
    account = db.get_account(conn, current_user["id"])
    balance = int(cu.aes_decrypt(SERVER_BALANCE_KEY, account["balance_nonce"], account["balance_ciphertext"]).decode())
    return UserResponse(id=current_user["id"], username=current_user["username"], balance=balance)
