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


ALICE_KEYS = {}
BOB_KEYS = {}


def ensure_demo_users():
    """Dang ky moi alice_xxx / bob_xxx cho lan chay nay, luu lai private key
    (client) tra ve TU MOT LAN DUY NHAT luc dang ky - giong nhu app that se
    luu private key trong secure storage cua nguoi dung, KHONG gui lai server."""
    for username, password, pin, store in [(ALICE, "alice123", "111111", ALICE_KEYS), (BOB, "bob123", "222222", BOB_KEYS)]:
        r = requests.post(f"{BASE}/register", json={"username": username, "password": password, "pin": pin})
        r.raise_for_status()
        store["private_key_pem"] = r.json()["private_key_pem"]
        store["id"] = r.json()["id"]  # id so - phai dung ID nay khi ky, giong het server dung khi verify


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
# Helper: CLIENT tu tao + ky payload (dung crypto_utils, private key CHI
# client giu - khong gui private key len server o buoc nay)
# =====================================================================
def client_build_signed_payload(sender_id, receiver_id, amount, private_key_pem):
    return cu.build_transaction_payload(sender_id, receiver_id, amount, private_key_pem)


# =====================================================================
# DEMO 2: MITM sua doi request tren duong truyen (attacker doi so tien)
# Dung endpoint /transfer-signed: client da ky TRUOC KHI gui, server chi verify
# =====================================================================
def demo_2_mitm_http_tamper():
    line("DEMO 2 (TAN CONG - tang HTTP, endpoint /transfer-signed): Attacker sua 'amount' sau khi da ky")
    token = login(ALICE, "alice123")
    bal_before = get_balance(token)

    # CLIENT (alice) tu tao va ky giao dich THAT (100k) truoc khi gui di
    payload = client_build_signed_payload(ALICE_KEYS["id"], BOB_KEYS["id"], 100000, ALICE_KEYS["private_key_pem"])
    original_body = {**payload, "receiver_username": BOB, "pin": "111111", "description": "chuyen 100k"}
    print("Request da duoc client ky (amount that = 100,000):")
    print(f"  amount={payload['amount']}, data_hash={payload['data_hash'][:24]}...")

    tampered_body = copy.deepcopy(original_body)
    tampered_body["amount"] = 9000000  # attacker doi 100k -> 9 trieu SAU KHI da ky
    print("Attacker chan tren duong truyen va sua amount -> 9,000,000 (khong the ky lai vi khong co private key alice)")

    r = requests.post(f"{BASE}/transfer-signed", headers={"Authorization": f"Bearer {token}"}, json=tampered_body)
    print("HTTP status:", r.status_code)
    print("Ket qua:", r.json())
    bal_after = get_balance(token)
    print(f"So du alice: {bal_before:,} -> {bal_after:,} VND (khong doi neu bi chan dung)")

    print("\n[NHAN XET] Vi transaction_id/nonce/timestamp/data_hash/signature da duoc CLIENT")
    print("(alice) tao va ky TRUOC KHI request roi khoi may, attacker sua 'amount' tren duong")
    print("truyen lam data_hash khong con khop voi noi dung moi -> verify_transaction_payload()")
    print("phat hien va tu choi NGAY BUOC DAU TIEN, truoc ca khi kiem tra PIN/so du.")


# =====================================================================
# DEMO 3: Replay - gui lai nguyen request da ky (dung endpoint /transfer-signed)
# =====================================================================
def demo_3_http_replay():
    line("DEMO 3 (TAN CONG - tang HTTP, endpoint /transfer-signed): Attacker gui lai (replay) request da ky")
    token = login(ALICE, "alice123")
    bal_before = get_balance(token)

    payload = client_build_signed_payload(ALICE_KEYS["id"], BOB_KEYS["id"], 200000, ALICE_KEYS["private_key_pem"])
    body = {**payload, "receiver_username": BOB, "pin": "111111", "description": "replay test"}

    r1 = requests.post(f"{BASE}/transfer-signed", headers={"Authorization": f"Bearer {token}"}, json=body)
    print("Lan gui 1 (that):", r1.status_code, "- tx_id:", r1.json().get("transaction_id"))

    r2 = requests.post(f"{BASE}/transfer-signed", headers={"Authorization": f"Bearer {token}"}, json=body)
    print("Lan gui 2 (attacker bat lai va gui lai y nguyen):", r2.status_code, "-", r2.json().get("detail") or r2.json().get("transaction_id"))

    bal_after = get_balance(token)
    print(f"So du alice: {bal_before:,} -> {bal_after:,} VND (chi tru 1 lan neu replay bi chan dung)")

    print("\n[NHAN XET] Vi nonce do CHINH CLIENT sinh ra va co dinh tu luc ky, request lap lai")
    print("mang CUNG 1 nonce -> DBNonceTracker nhan ra nonce nay da duoc dung (tu lan gui dau)")
    print("va tu choi ngay, KHONG tao them giao dich moi. Replay bi chan dung o ca tang HTTP.")


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
