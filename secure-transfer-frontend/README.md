# Secure Transfer System - Frontend

React/Vite frontend for the simulated secure money-transfer system.

## 1. Install

```bash
npm install
```

## 2. Run with mock data

Create `.env` from `.env.example` and keep:

```env
VITE_USE_MOCK=true
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Then:

```bash
npm run dev
```

Open the URL shown by Vite. Demo login:

- Username: `user1`
- Password: `123456`
- Transfer PIN: `123456`

## 3. Connect to the real FastAPI backend

Set:

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8000
```

The frontend expects these endpoints:

- `POST /register`
- `POST /login`
- `GET /account`
- `GET /balance`
- `POST /transfer`
- `GET /transactions`
- `GET /transactions/{transaction_id}`

The login response should provide `access_token`. The frontend sends it as a Bearer token.
Transfer requests also include a six-digit `pin` field, which the backend must validate before creating the transaction.

## 4. Security fields shown by the UI

Transaction detail can display:

- SHA-256 hash validity
- RSA digital signature validity
- Replay-protection result
- transaction_id, nonce, timestamp

The frontend does not implement RSA/AES itself; those checks belong to the backend/security layer.
