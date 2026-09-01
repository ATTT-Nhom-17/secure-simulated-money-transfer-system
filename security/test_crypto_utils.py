import copy
import time
import base64

from cryptography.exceptions import InvalidTag
import crypto_utils as cu


def check(label, ok):
    print(("OK   " if ok else "FAIL "), label)


def test_sign_verify():
    priv, pub = cu.generate_rsa_keypair()
    msg = b"chuyen 500000 tu A sang B"
    sig = cu.sign_data(priv, msg)
    check("ky va verify chu ky dung", cu.verify_signature(pub, msg, sig))

    # thu doi noi dung xem chu ky cu co con verify duoc khong
    msg_fake = b"chuyen 5000000 tu A sang B"
    check("phat hien duoc khi noi dung bi doi", not cu.verify_signature(pub, msg_fake, sig))


def test_aes():
    key = cu.generate_aes_key()
    plaintext = b"so du: 1250000"
    enc = cu.aes_encrypt(key, plaintext)
    out = cu.aes_decrypt(key, enc["nonce"], enc["ciphertext"])
    check("AES ma hoa/giai ma dung nhu ban goc", out == plaintext)

    # sua 1 byte trong ciphertext xem GCM co bat duoc khong
    raw = bytearray(base64.b64decode(enc["ciphertext"]))
    raw[0] ^= 0xFF
    fake_ct = base64.b64encode(bytes(raw)).decode()
    try:
        cu.aes_decrypt(key, enc["nonce"], fake_ct)
        check("phat hien ciphertext bi sua", False)
    except InvalidTag:
        check("phat hien ciphertext bi sua", True)


def test_key_wrap():
    priv, pub = cu.generate_rsa_keypair()
    aes_key = cu.generate_aes_key()
    wrapped = cu.rsa_encrypt_key(pub, aes_key)
    got_back = cu.rsa_decrypt_key(priv, wrapped)
    check("khoa AES sau khi boc/mo bang RSA khong doi", got_back == aes_key)


def test_password():
    h = cu.hash_password("MatKhau123!")
    check("dang nhap dung mat khau", cu.verify_password("MatKhau123!", h))
    check("dang nhap sai mat khau bi tu choi", not cu.verify_password("random123", h))


def test_transaction_hop_le():
    priv, pub = cu.generate_rsa_keypair()
    tracker = cu.NonceTracker()
    payload = cu.build_transaction_payload("tk_A", "tk_B", 500000, priv)
    try:
        cu.verify_transaction_payload(payload, pub, tracker)
        check("giao dich hop le duoc chap nhan", True)
    except cu.TransactionError as e:
        check(f"giao dich hop le duoc chap nhan (loi: {e})", False)


def test_gia_lap_sua_goi_tin():
    # gia su hacker chan giao dich, doi so tien roi gui tiep cho server
    priv, pub = cu.generate_rsa_keypair()
    tracker = cu.NonceTracker()
    payload = cu.build_transaction_payload("tk_A", "tk_B", 500000, priv)

    payload_bi_sua = copy.deepcopy(payload)
    payload_bi_sua["amount"] = 50000000

    try:
        cu.verify_transaction_payload(payload_bi_sua, pub, tracker)
        check("chan duoc giao dich bi sua so tien", False)
    except cu.TransactionError:
        check("chan duoc giao dich bi sua so tien", True)


def test_gia_lap_replay():
    # hacker khong sua gi ca, chi bat lai goi tin cu roi gui lai y het
    priv, pub = cu.generate_rsa_keypair()
    tracker = cu.NonceTracker()
    payload = cu.build_transaction_payload("tk_A", "tk_B", 500000, priv)

    cu.verify_transaction_payload(payload, pub, tracker)  # lan dau, hop le binh thuong

    try:
        cu.verify_transaction_payload(payload, pub, tracker)  # gui lai lan 2
        check("chan duoc replay attack", False)
    except cu.TransactionError:
        check("chan duoc replay attack", True)


def test_goi_tin_cu():
    priv, pub = cu.generate_rsa_keypair()
    tracker = cu.NonceTracker()
    payload = cu.build_transaction_payload("tk_A", "tk_B", 500000, priv)
    payload["timestamp"] = time.time() - 3600  # gia lap goi tin tu 1 tieng truoc

    try:
        cu.verify_transaction_payload(payload, pub, tracker)
        check("chan duoc goi tin qua cu", False)
    except cu.TransactionError:
        check("chan duoc goi tin qua cu", True)


if __name__ == "__main__":
    test_sign_verify()
    test_aes()
    test_key_wrap()
    test_password()
    test_transaction_hop_le()
    test_gia_lap_sua_goi_tin()
    test_gia_lap_replay()
    test_goi_tin_cu()
