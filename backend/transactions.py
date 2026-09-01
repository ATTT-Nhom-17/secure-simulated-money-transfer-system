import os
import sys
from typing import List

from fastapi import APIRouter, Depends, HTTPException

# tro toi 2 thu muc db/ va security/ de import duoc db.py va crypto_utils.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "db"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "security"))
import db
import crypto_utils as cu
from database import get_db
from config import SERVER_BALANCE_KEY
from schemas import TransferRequest, TransactionResponse, TransactionListResponse
from auth import get_current_user, get_user_balance

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/transfer", response_model=TransactionResponse)
def transfer(req: TransferRequest, current_user=Depends(get_current_user), conn=Depends(get_db)):
    # 1. Khong tu chuyen cho chinh minh
    if req.receiver_username == current_user["username"]:
        raise HTTPException(status_code=400, detail="Không thể tự chuyển tiền cho chính mình")

    # 2. Amount > 0
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Số tiền chuyển phải lớn hơn 0")

    # 3. Verify PIN
    if not current_user["pin_hash"] or not cu.verify_password(req.pin, current_user["pin_hash"]):
        raise HTTPException(status_code=400, detail="Mã PIN không chính xác")

    # 4. Nguoi nhan ton tai trong DB
    receiver = db.get_user_by_username(conn, req.receiver_username)
    if not receiver:
        raise HTTPException(status_code=404, detail="Người nhận không tồn tại")

    # 5. Du so du (giai ma tu AES-GCM trong bang accounts)
    sender_balance = get_user_balance(conn, current_user["id"])

    if sender_balance < req.amount:
        raise HTTPException(status_code=400, detail="Số dư không đủ để thực hiện giao dịch")

    # 6. Build giao dich bang crypto_utils (ky bang private key cua nguoi gui)
    payload = cu.build_transaction_payload(
        sender_id=current_user["id"],
        receiver_id=receiver["id"],
        amount=req.amount,
        sender_private_key_pem=current_user["private_key_pem"],
    )

    # 7. Verify giao dich bang crypto_utils + DBNonceTracker
    tracker = db.DBNonceTracker(conn)
    try:
        cu.verify_transaction_payload(payload, current_user["public_key_pem"], tracker)
    except cu.TransactionError as e:
        # Ghi log giao dich bi tu choi vao audit trail DB
        db.insert_transaction(conn, payload, status="rejected", reject_reason=str(e), description=req.description)
        raise HTTPException(status_code=400, detail=f"Xác minh giao dịch thất bại: {str(e)}")

    # 8. Moi that su tru/cong tien (ma hoa lai bang AES-256-GCM) va luu vao DB
    new_sender_balance = sender_balance - req.amount
    enc_sender = cu.aes_encrypt(SERVER_BALANCE_KEY, str(new_sender_balance).encode())
    db.update_balance(conn, current_user["id"], enc_sender["nonce"], enc_sender["ciphertext"])

    receiver_balance = get_user_balance(conn, receiver["id"])
    new_receiver_balance = receiver_balance + req.amount
    enc_receiver = cu.aes_encrypt(SERVER_BALANCE_KEY, str(new_receiver_balance).encode())
    db.update_balance(conn, receiver["id"], enc_receiver["nonce"], enc_receiver["ciphertext"])

    # Ghi log giao dich thanh cong
    db.insert_transaction(conn, payload, status="success", description=req.description)

    return TransactionResponse(
        transaction_id=payload["transaction_id"],
        sender=current_user["username"],
        receiver=receiver["username"],
        sender_id=current_user["id"],
        receiver_id=receiver["id"],
        amount=req.amount,
        description=req.description,
        nonce=payload["nonce"],
        timestamp=payload["timestamp"],
        data_hash=payload["data_hash"],
        signature=payload["signature"],
        status="SUCCESS",
        signature_valid=True,
        hash_valid=True,
        replay_detected=False,
        hash=payload["data_hash"],
    )


@router.get("/history", response_model=TransactionListResponse)
def get_history(current_user=Depends(get_current_user), conn=Depends(get_db)):
    rows = db.get_transactions_for_user(conn, current_user["id"])
    result = []
    for r in rows:
        r_dict = dict(r)
        result.append(TransactionResponse(
            transaction_id=r_dict["transaction_id"],
            sender=r_dict["sender_username"],
            receiver=r_dict["receiver_username"],
            sender_id=r_dict["sender_id"],
            receiver_id=r_dict["receiver_id"],
            amount=r_dict["amount"],
            description=r_dict.get("description") or "",
            nonce=r_dict["nonce"],
            timestamp=r_dict["timestamp"],
            data_hash=r_dict["data_hash"],
            signature=r_dict["signature"],
            status=r_dict["status"].upper(),
            reject_reason=r_dict.get("reject_reason"),
            created_at=r_dict.get("created_at"),
            signature_valid=(r_dict["status"] == "success"),
            hash_valid=(r_dict["status"] == "success"),
            replay_detected=(r_dict.get("reject_reason") is not None and "replay" in r_dict.get("reject_reason").lower()),
            hash=r_dict["data_hash"],
        ))
    return TransactionListResponse(transactions=result)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_detail(transaction_id: str, current_user=Depends(get_current_user), conn=Depends(get_db)):
    row = db.get_transaction_by_id(conn, transaction_id)
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")

    r_dict = dict(row)
    if r_dict["sender_id"] != current_user["id"] and r_dict["receiver_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem giao dịch này")

    # Kiem tra xac thuc chu ky va hash tu du lieu goc
    msg = cu.canonical_transaction_string(
        r_dict["transaction_id"], r_dict["sender_id"], r_dict["receiver_id"],
        r_dict["amount"], r_dict["nonce"], r_dict["timestamp"],
    )
    computed_hash = cu.sha256_hash(msg)
    hash_valid = (computed_hash == r_dict["data_hash"])
    signature_valid = cu.verify_signature(r_dict["sender_public_key_pem"], msg, r_dict["signature"])
    replay_detected = (r_dict.get("reject_reason") is not None and "replay" in r_dict.get("reject_reason").lower())

    return TransactionResponse(
        transaction_id=r_dict["transaction_id"],
        sender=r_dict["sender_username"],
        receiver=r_dict["receiver_username"],
        sender_id=r_dict["sender_id"],
        receiver_id=r_dict["receiver_id"],
        amount=r_dict["amount"],
        description=r_dict.get("description") or "",
        nonce=r_dict["nonce"],
        timestamp=r_dict["timestamp"],
        data_hash=r_dict["data_hash"],
        signature=r_dict["signature"],
        status=r_dict["status"].upper(),
        reject_reason=r_dict.get("reject_reason"),
        created_at=r_dict.get("created_at"),
        signature_valid=signature_valid,
        hash_valid=hash_valid,
        replay_detected=replay_detected,
        hash=r_dict["data_hash"],
    )

