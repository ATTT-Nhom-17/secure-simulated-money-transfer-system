"""
DEMO TAN CONG & BAO VE - He thong chuyen tien gia lap (RSA + AES)
Chay script nay khi backend (uvicorn main:app) da chay o http://127.0.0.1:8000
va da co san 2 user 'alice' / 'bob' (dang ky qua /register).

Cach chay:
    python attack_demo.py
"""
import copy
import os
import sys
import time

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import crypto_utils as cu

BASE = "http://127.0.0.1:8000"

# username sinh ngau nhien theo lan chay, de chay lai nhieu lan khong bi loi
# "username da ton tai" va luon bat dau voi so du day du 10,000,000 VND
_SUFFIX = str(int(time.time()))[-6:]
ALICE = f"alice_{_SUFFIX}"
BOB = f"bob_{_SUFFIX}"


def ensure_demo_users():
    """Dang ky moi alice_xxx / bob_xxx cho lan chay nay."""
    for username, password, pin in [(ALICE, "alice123", "111111"), (BOB, "bob123", "222222")]:
        r = requests.post(f"{BASE}/register", json={"username": username, "password": password, "pin": pin})
        r.raise_for_status()


def line(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def login(username, password):
    r = requests.post(f"{BASE}/login", json={"username": username, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def get_balance(token):
    r = requests.get(f"{BASE}/balance", headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json()["balance"]


# =====================================================================
# DEMO 1: Giao dich hop le (baseline)
# =====================================================================
def demo_1_normal_transfer():
    line("DEMO 1: Giao dich chuyen tien hop le")
    token = login(ALICE, "alice123")
    bal_before = get_balance(token)
    print(f"So du alice truoc: {bal_before:,} VND")

    r = requests.post(
        f"{BASE}/transfer",
        headers={"Authorization": f"Bearer {token}"},
        json={"receiver_username": BOB, "amount": 500000, "pin": "111111", "description": "demo hop le"},
    )
    print("HTTP status:", r.status_code)
    print("Ket qua:", r.json())

    bal_after = get_balance(token)
    print(f"So du alice sau : {bal_after:,} VND (tru {bal_before - bal_after:,} VND)")
    return r.json()


# =====================================================================
# DEMO 2: MITM sua doi request tren duong truyen (attacker doi so tien)
# =====================================================================
def demo_2_mitm_http_tamper():
    line("DEMO 2 (TAN CONG - tang HTTP): Attacker chan va sua 'amount' truoc khi toi server")
    token = login(ALICE, "alice123")
    bal_before = get_balance(token)

    original_body = {"receiver_username": BOB, "amount": 100000, "pin": "111111", "description": "chuyen 100k"}
    tampered_body = copy.deepcopy(original_body)
    tampered_body["amount"] = 9000000  # attacker doi 100k -> 9 trieu
    print("Request goc attacker chan duoc :", original_body)
    print("Request sau khi attacker sua   :", tampered_body)

    r = requests.post(
        f"{BASE}/transfer",
        headers={"Authorization": f"Bearer {token}"},
        json=tampered_body,
    )
    print("HTTP status:", r.status_code)
    print("Ket qua:", r.json())
    bal_after = get_balance(token)
    print(f"So du alice: {bal_before:,} -> {bal_after:,} VND")

    print("\n[NHAN XET] O kien truc hien tai, transaction_id/nonce/signature duoc SERVER tu sinh")
    print("SAU KHI nhan request, tu chinh 'amount' ma attacker da sua - nen server ky dung so")
    print("tien attacker gui, KHONG phat hien duoc tampering o tang HTTP nay. Day la ly do bat")
    print("buoc PHAI dung HTTPS/TLS cho kenh client-server; chu ky RSA trong do an nay bao ve")
    print("tinh toan ven CUA BAN GHI GIAO DICH SAU KHI da duoc tao (audit trail), khong thay the")
    print("cho TLS o tang van chuyen. Xem DEMO 4 de thay dung cach chu ky phat hien tampering.")


# =====================================================================
# DEMO 3: Replay - gui lai nguyen request HTTP da chan duoc
# =====================================================================
def demo_3_http_replay():
    line("DEMO 3 (TAN CONG - tang HTTP): Attacker gui lai (replay) nguyen request da chan duoc")
    token = login(ALICE, "alice123")
    bal_before = get_balance(token)
    body = {"receiver_username": BOB, "amount": 200000, "pin": "111111", "description": "replay test"}

    r1 = requests.post(f"{BASE}/transfer", headers={"Authorization": f"Bearer {token}"}, json=body)
    print("Lan gui 1 (that):", r1.status_code, "- tx_id:", r1.json().get("transaction_id"))

    r2 = requests.post(f"{BASE}/transfer", headers={"Authorization": f"Bearer {token}"}, json=body)
    print("Lan gui 2 (attacker replay y nguyen):", r2.status_code, "- tx_id:", r2.json().get("transaction_id"))

    bal_after = get_balance(token)
    print(f"So du alice: {bal_before:,} -> {bal_after:,} VND (bi tru 2 lan neu replay khong bi chan)")

    print("\n[NHAN XET] NonceTracker chi chan duoc khi 2 lan verify dung CHUNG 1 nonce. O day")
    print("nonce duoc SERVER SINH MOI trong build_transaction_payload() moi khi /transfer duoc")
    print("goi, nen 2 request giong het nhau van tao ra 2 giao dich HOP LE khac nhau -> KHONG")
    print("phai la 'replay bi chan', ma la 2 giao dich that su khac nhau ve mat he thong.")
    print("Co che chong-replay hien co bao ve dung thu: 'khong the phat lai 1 GIAO DICH DA KY'")
    print("(xem DEMO 4). De chan duoc ca replay o tang HTTP, can them 1 idempotency-key do")
    print("CLIENT sinh va gui kem request, server luu lai va tu choi request trung key.")


# =====================================================================
# DEMO 4: Dung dung tang crypto_utils - noi chu ky/nonce THAT SU bao ve
# =====================================================================
def demo_4_crypto_layer_attacks():
    line("DEMO 4 (BAO VE - tang crypto): Kiem tra truc tiep engine ky so / chong replay")

    priv_pem, pub_pem = cu.generate_rsa_keypair()
    attacker_priv_pem, attacker_pub_pem = cu.generate_rsa_keypair()
    tracker = cu.NonceTracker()

    # --- 4a: giao dich hop le ---
    payload = cu.build_transaction_payload("acc_alice", "acc_bob", 500000, priv_pem)
    cu.verify_transaction_payload(payload, pub_pem, tracker)
    print("[4a] Giao dich hop le -> XAC MINH THANH CONG")

    # --- 4b: tampering sau khi ky (sua amount, KHONG ky lai) ---
    tampered = copy.deepcopy(payload)
    tampered["amount"] = 50000000
    tampered["transaction_id"] = cu.generate_transaction_id()  # tranh trung nonce voi 4a
    tampered["nonce"] = cu.generate_nonce()
    tampered["timestamp"] = time.time()
    # attacker sua so tien nhung KHONG co private key cua alice de ky lai cho dung
    # -> data_hash/signature cu khong con khop voi noi dung moi
    tampered["data_hash"] = payload["data_hash"]
    tampered["signature"] = payload["signature"]
    try:
        cu.verify_transaction_payload(tampered, pub_pem, tracker)
        print("[4b] LOI: tampering KHONG bi phat hien!")
    except cu.TransactionError as e:
        print(f"[4b] Sua amount ma khong ky lai -> BI CHAN: {e}")

    # --- 4c: gia mao chu ky bang khoa khac (khong co private key that) ---
    forged = cu.build_transaction_payload("acc_alice", "acc_bob", 999999, attacker_priv_pem)
    try:
        # verify bang public key THAT cua alice, nhung chu ky lai duoc ky boi khoa attacker
        cu.verify_transaction_payload(forged, pub_pem, tracker)
        print("[4c] LOI: chu ky gia mao KHONG bi phat hien!")
    except cu.TransactionError as e:
        print(f"[4c] Attacker tu ky bang khoa rieng cua no (khong co private key alice) -> BI CHAN: {e}")

    # --- 4d: replay dung nonce da dung ---
    replay_payload = cu.build_transaction_payload("acc_alice", "acc_bob", 300000, priv_pem)
    cu.verify_transaction_payload(replay_payload, pub_pem, tracker)
    print("[4d] Giao dich that lan 1 -> THANH CONG")
    try:
        cu.verify_transaction_payload(replay_payload, pub_pem, tracker)
        print("[4d] LOI: replay KHONG bi phat hien!")
    except cu.TransactionError as e:
        print(f"[4d] Gui lai y nguyen payload da ky (replay) -> BI CHAN: {e}")

    # --- 4e: timestamp qua han (chong goi tin cu bi bat lai gui muon) ---
    old_payload = cu.build_transaction_payload("acc_alice", "acc_bob", 100000, priv_pem)
    old_payload["timestamp"] = time.time() - 999  # gia lap goi tin 999s truoc
    msg = cu.canonical_transaction_string(
        old_payload["transaction_id"], old_payload["sender_id"], old_payload["receiver_id"],
        old_payload["amount"], old_payload["nonce"], old_payload["timestamp"],
    )
    old_payload["data_hash"] = cu.sha256_hash(msg)
    old_payload["signature"] = cu.sign_data(priv_pem, msg)
    try:
        cu.verify_transaction_payload(old_payload, pub_pem, tracker)
        print("[4e] LOI: goi tin qua han KHONG bi phat hien!")
    except cu.TransactionError as e:
        print(f"[4e] Goi tin cu (timestamp qua han) -> BI CHAN: {e}")


# =====================================================================
# DEMO 5: Sua truc tiep du lieu trong DB (attacker co quyen ghi DB) ->
# phat hien qua audit trail khi tra cuu lai chi tiet giao dich
# =====================================================================
def demo_5_db_tamper_detection():
    line("DEMO 5 (BAO VE - audit trail): Sua truc tiep ban ghi trong DB, kiem tra lai qua API")
    token = login(BOB, "bob123")
    r = requests.post(
        f"{BASE}/transfer",
        headers={"Authorization": f"Bearer {token}"},
        json={"receiver_username": ALICE, "amount": 50000, "pin": "222222", "description": "demo db tamper"},
    )
    tx = r.json()
    tx_id = tx["transaction_id"]
    print(f"Da tao giao dich {tx_id}, amount that = {tx['amount']:,} VND")

    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), "..", "db", "transfer_system.db")
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE transactions SET amount = ? WHERE transaction_id = ?", (99999999, tx_id))
    conn.commit()
    conn.close()
    print("Attacker (co quyen ghi thang vao DB) da sua amount thanh 99,999,999 VND")

    r2 = requests.get(f"{BASE}/transactions/{tx_id}", headers={"Authorization": f"Bearer {token}"})
    detail = r2.json()
    print(f"API tra ve amount = {detail['amount']:,}, hash_valid = {detail['hash_valid']}, "
          f"signature_valid = {detail['signature_valid']}")
    if not detail["hash_valid"] and not detail["signature_valid"]:
        print("[5] Sua du lieu truc tiep trong DB -> BI PHAT HIEN qua hash/chu ky khong con khop")
    else:
        print("[5] CANH BAO: sua DB ma khong bi phat hien")


if __name__ == "__main__":
    ensure_demo_users()
    demo_1_normal_transfer()
    demo_2_mitm_http_tamper()
    demo_3_http_replay()
    demo_4_crypto_layer_attacks()
    demo_5_db_tamper_detection()
    line("HOAN TAT DEMO")
