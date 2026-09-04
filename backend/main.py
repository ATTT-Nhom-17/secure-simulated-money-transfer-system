import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# tro toi 2 thu muc db/ va security/ de import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "db"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "security"))
import db
import crypto_utils as cu
from config import SERVER_BALANCE_KEY
from database import get_db
from schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    AccountResponse, BalanceResponse, TransferRequest, SignedTransferRequest, TransactionResponse, TransactionListResponse
)
from auth import (
    router as auth_router, register as auth_register, login as auth_login,
    get_me as auth_get_me, get_current_user, get_user_balance
)
from transactions import router as transactions_router, transfer as tx_transfer, transfer_signed as tx_transfer_signed, get_history as tx_get_history, get_transaction_detail as tx_get_detail


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khoi tao Database khi startup
    db.init_db()
    print("Database SQLite initialized successfully.")
    yield


app = FastAPI(
    title="Secure Simulated Money Transfer System API",
    description="Hệ thống mô phỏng chuyển tiền an toàn với RSA, AES-256-GCM, SHA-256, Bcrypt và Replay Protection.",
    version="1.0.0",
    lifespan=lifespan,
)

# Cau hinh CORS cho Frontend (React/Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dang ky cac router chinh
app.include_router(auth_router)
app.include_router(transactions_router)


# ===== ROOT / COMPATIBILITY ALIAS ENDPOINTS CHO FRONTEND =====

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Secure Simulated Money Transfer API",
        "docs": "/docs",
    }


@app.post("/register", response_model=UserResponse, tags=["compatibility"])
def root_register(req: RegisterRequest, conn=Depends(get_db)):
    return auth_register(req, conn)


@app.post("/login", response_model=TokenResponse, tags=["compatibility"])
def root_login(req: LoginRequest, conn=Depends(get_db)):
    return auth_login(req, conn)


@app.get("/account", response_model=AccountResponse, tags=["compatibility"])
def root_account(current_user=Depends(get_current_user), conn=Depends(get_db)):
    balance = get_user_balance(conn, current_user["id"])
    return AccountResponse(username=current_user["username"], balance=balance)


@app.get("/balance", response_model=BalanceResponse, tags=["compatibility"])
def root_balance(current_user=Depends(get_current_user), conn=Depends(get_db)):
    balance = get_user_balance(conn, current_user["id"])
    return BalanceResponse(balance=balance)


@app.post("/transfer", response_model=TransactionResponse, tags=["compatibility"])
def root_transfer(req: TransferRequest, current_user=Depends(get_current_user), conn=Depends(get_db)):
    return tx_transfer(req, current_user, conn)


@app.post("/transfer-signed", response_model=TransactionResponse, tags=["compatibility"])
def root_transfer_signed(req: SignedTransferRequest, current_user=Depends(get_current_user), conn=Depends(get_db)):
    return tx_transfer_signed(req, current_user, conn)


@app.get("/transactions", response_model=TransactionListResponse, tags=["compatibility"])
def root_transactions(current_user=Depends(get_current_user), conn=Depends(get_db)):
    return tx_get_history(current_user, conn)


@app.get("/transactions/{transaction_id}", response_model=TransactionResponse, tags=["compatibility"])
def root_transaction_detail(transaction_id: str, current_user=Depends(get_current_user), conn=Depends(get_db)):
    return tx_get_detail(transaction_id, current_user, conn)


if __name__ == "__main__":
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=backend_dir)

