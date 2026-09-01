from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


# ===== AUTH SCHEMAS =====

class RegisterRequest(BaseModel):
    username: str
    password: str
    pin: str = Field(default="123456", description="Mã PIN 6 chữ số")
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    balance: int


class AccountResponse(BaseModel):
    username: str
    email: Optional[str] = None
    balance: int


class BalanceResponse(BaseModel):
    balance: int


# ===== TRANSFER & TRANSACTION SCHEMAS =====

class TransferRequest(BaseModel):
    receiver_username: Optional[str] = None
    receiver: Optional[str] = None
    amount: int
    pin: str = Field(default="123456", description="Mã PIN 6 chữ số")
    description: Optional[str] = ""

    @model_validator(mode="after")
    def populate_receiver(self):
        target = self.receiver_username or self.receiver
        if not target:
            raise ValueError("Người nhận (receiver) không được để trống")
        self.receiver_username = target
        self.receiver = target
        return self


class TransactionResponse(BaseModel):
    transaction_id: str
    sender: str
    receiver: str
    sender_id: int
    receiver_id: int
    amount: int
    description: Optional[str] = None
    nonce: str
    timestamp: float | str
    data_hash: str
    signature: str
    status: str
    reject_reason: Optional[str] = None
    created_at: Optional[float | str] = None
    # Các trường hiển thị an ninh cho Frontend (Security Verification UI)
    signature_valid: bool = True
    hash_valid: bool = True
    replay_detected: bool = False
    hash: Optional[str] = None


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]

