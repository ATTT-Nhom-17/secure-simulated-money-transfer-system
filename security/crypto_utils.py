import base64
import hashlib
import os
import time
import uuid

import bcrypt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# module security cho do an chuyen tien - phan cua minh (Nguoi 2)
# RSA de ky/xac minh giao dich va trao doi khoa AES
# AES-256-GCM de ma hoa du lieu (nhanh hon RSA nhieu, RSA chi dung cho khoa)


def generate_rsa_keypair(key_size=2048):
    # tra ve dang PEM (string) de con gui qua socket / luu file duoc
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def load_private_key(pem_text):
    return serialization.load_pem_private_key(pem_text.encode(), password=None)


def load_public_key(pem_text):
    return serialization.load_pem_public_key(pem_text.encode())


# dung RSA de "boc" khoa AES truoc khi gui di, khong dung RSA ma hoa het du lieu
# vi RSA cham va gioi han dung luong dau vao (chi hop voi block nho nhu 1 cai key)

def rsa_encrypt_key(public_key_pem, raw_key):
    pub = load_public_key(public_key_pem)
    ct = pub.encrypt(
        raw_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return base64.b64encode(ct).decode()


def rsa_decrypt_key(private_key_pem, encrypted_key_b64):
    priv = load_private_key(private_key_pem)
    ct = base64.b64decode(encrypted_key_b64)
    return priv.decrypt(
        ct,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


def sign_data(private_key_pem, data: bytes):
    priv = load_private_key(private_key_pem)
    sig = priv.sign(
        data,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode()


def verify_signature(public_key_pem, data: bytes, signature_b64):
    pub = load_public_key(public_key_pem)
    sig = base64.b64decode(signature_b64)
    try:
        pub.verify(
            sig, data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False


def sha256_hash(data: bytes):
    return hashlib.sha256(data).hexdigest()


def canonical_transaction_string(transaction_id, sender_id, receiver_id, amount, nonce, timestamp):
    # ghep theo 1 thu tu co dinh de ca 2 ben (nguoi ky va nguoi xac minh) hash ra cung 1 gia tri
    # neu doi thu tu hoac dau phan cach o day thi phai doi dong bo ca 2 ben, khong thi verify se luon fail
    raw = f"{transaction_id}|{sender_id}|{receiver_id}|{amount}|{nonce}|{timestamp}"
    return raw.encode()


def generate_aes_key():
    return AESGCM.generate_key(bit_length=256)


def aes_encrypt(key, plaintext: bytes, associated_data=None):
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # nonce phai random moi lan, khong duoc tai su dung voi cung 1 key
    ct = aesgcm.encrypt(nonce, plaintext, associated_data)
    return {
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ct).decode(),
    }


def aes_decrypt(key, nonce_b64, ciphertext_b64, associated_data=None):
    # neu ciphertext bi sua du 1 bit thi ham nay se raise InvalidTag - do la co che
    # chong tampering cua GCM, khong can tu code them check gi ca
    aesgcm = AESGCM(key)
    nonce = base64.b64decode(nonce_b64)
    ct = base64.b64decode(ciphertext_b64)
    return aesgcm.decrypt(nonce, ct, associated_data)


def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def generate_transaction_id():
    return str(uuid.uuid4())


def generate_nonce():
    return base64.b64encode(os.urandom(16)).decode()


class TransactionError(Exception):
    pass


class NonceTracker:
    # luu lai nonce da dung roi de phat hien replay attack
    # luu y: phai la 1 instance duy nhat song suot doi server, khong duoc tao moi
    # moi lan verify - neu tao moi thi lich su nonce mat het, replay se lot qua duoc

    def __init__(self, max_age_seconds=300):
        self.max_age_seconds = max_age_seconds
        self._used = {}

    def _purge_expired(self, now):
        for n in [n for n, t in self._used.items() if now - t > self.max_age_seconds]:
            del self._used[n]

    def seen(self, nonce):
        return nonce in self._used

    def mark_used(self, nonce, timestamp):
        self._purge_expired(timestamp)
        self._used[nonce] = timestamp


def build_transaction_payload(sender_id, receiver_id, amount, sender_private_key_pem):
    transaction_id = generate_transaction_id()
    nonce = generate_nonce()
    timestamp = time.time()

    msg = canonical_transaction_string(transaction_id, sender_id, receiver_id, amount, nonce, timestamp)
    data_hash = sha256_hash(msg)
    signature = sign_data(sender_private_key_pem, msg)

    return {
        "transaction_id": transaction_id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "amount": amount,
        "nonce": nonce,
        "timestamp": timestamp,
        "data_hash": data_hash,
        "signature": signature,
    }


def verify_transaction_payload(payload, sender_public_key_pem, nonce_tracker, max_clock_skew_seconds=300):
    for field in ("transaction_id", "sender_id", "receiver_id", "amount", "nonce", "timestamp", "data_hash", "signature"):
        if field not in payload:
            raise TransactionError(f"thieu field: {field}")

    now = time.time()
    if abs(now - payload["timestamp"]) > max_clock_skew_seconds:
        # cai nay bat duoc ca goi tin cu bi bat lai gui sau, khong chi replay ngay lap tuc
        raise TransactionError("timestamp qua han, co the la goi tin cu bi replay")

    if nonce_tracker.seen(payload["nonce"]):
        raise TransactionError("nonce da duoc dung roi - replay attack")

    msg = canonical_transaction_string(
        payload["transaction_id"], payload["sender_id"], payload["receiver_id"],
        payload["amount"], payload["nonce"], payload["timestamp"],
    )

    if sha256_hash(msg) != payload["data_hash"]:
        raise TransactionError("hash khong khop - du lieu bi sua doi tren duong truyen")

    if not verify_signature(sender_public_key_pem, msg, payload["signature"]):
        raise TransactionError("chu ky khong hop le")

    # den day moi coi la hop le, luc nay moi danh dau nonce la da dung
    nonce_tracker.mark_used(payload["nonce"], payload["timestamp"])
