import axios from 'axios';

const USE_MOCK = String(import.meta.env.VITE_USE_MOCK ?? 'true') === 'true';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Request failed';
    return Promise.reject(new Error(message));
  }
);

const delay = (ms = 350) => new Promise((resolve) => setTimeout(resolve, ms));

const defaultData = {
  username: 'user1',
  email: 'user1@example.com',
  balance: 10000000,
  transactions: [
    {
      transaction_id: 'TX001', sender: 'user1', receiver: 'user2', amount: 500000,
      description: 'Transfer for demo', timestamp: '2026-08-26T13:00:00Z', status: 'SUCCESS',
      signature_valid: true, hash_valid: true, replay_detected: false, nonce: 'NONCE001',
      signature: 'DEMO_RSA_SIGNATURE_TX001', hash: 'SHA256_DEMO_HASH_TX001'
    },
    {
      transaction_id: 'TX002', sender: 'user2', receiver: 'user1', amount: 200000,
      description: 'Refund', timestamp: '2026-08-25T09:45:00Z', status: 'SUCCESS',
      signature_valid: true, hash_valid: true, replay_detected: false, nonce: 'NONCE002',
      signature: 'DEMO_RSA_SIGNATURE_TX002', hash: 'SHA256_DEMO_HASH_TX002'
    },
    {
      transaction_id: 'TX003', sender: 'user1', receiver: 'user4', amount: 100000,
      description: 'Blocked example', timestamp: '2026-08-24T11:30:00Z', status: 'FAILED',
      signature_valid: false, hash_valid: false, replay_detected: false, nonce: 'NONCE003',
      signature: 'INVALID_SIGNATURE', hash: 'INVALID_HASH', error: 'Invalid digital signature'
    }
  ]
};

function loadMock() {
  const saved = localStorage.getItem('mockBankState');
  if (saved) return JSON.parse(saved);
  const state = structuredClone(defaultData);
  localStorage.setItem('mockBankState', JSON.stringify(state));
  return state;
}

function saveMock(state) {
  localStorage.setItem('mockBankState', JSON.stringify(state));
}

export async function login(credentials) {
  if (!USE_MOCK) {
    const res = (await client.post('/login', credentials)).data;
    if (res.access_token) {
      localStorage.setItem('token', res.access_token);
      localStorage.setItem('user', JSON.stringify({ username: res.username || credentials.username }));
    }
    return res;
  }
  await delay();
  if (!credentials.username || !credentials.password) throw new Error('Username and password are required.');
  if (credentials.username !== 'user1' || credentials.password !== '123456') {
    throw new Error('Invalid username or password. Demo account: user1 / 123456');
  }
  localStorage.setItem('token', 'demo-token');
  localStorage.setItem('user', JSON.stringify({ username: 'user1', email: 'user1@example.com' }));
  return { access_token: 'demo-token', username: 'user1' };
}

export async function register(payload) {
  if (!USE_MOCK) return (await client.post('/register', payload)).data;
  await delay();
  if (!payload.username || !payload.password) throw new Error('Username and password are required.');
  return { message: 'Registration successful' };
}

export async function getAccount() {
  if (!USE_MOCK) return (await client.get('/account')).data;
  await delay();
  const state = loadMock();
  return { username: state.username, email: state.email, balance: state.balance };
}

export async function getBalance() {
  if (!USE_MOCK) return (await client.get('/balance')).data;
  await delay();
  return { balance: loadMock().balance };
}

export async function transfer(payload) {
  if (!USE_MOCK) return (await client.post('/transfer', payload)).data;
  await delay();
  const state = loadMock();
  const amount = Number(payload.amount);
  if (!payload.receiver) throw new Error('Receiver is required.');
  if (!Number.isFinite(amount) || amount <= 0) throw new Error('Amount must be greater than 0.');
  if (amount > state.balance) throw new Error('Insufficient balance.');
  if (payload.receiver === state.username) throw new Error('You cannot transfer to yourself.');

  const id = `TX${String(state.transactions.length + 1).padStart(3, '0')}`;
  const tx = {
    transaction_id: id,
    sender: state.username,
    receiver: payload.receiver,
    amount,
    description: payload.description || '',
    timestamp: new Date().toISOString(),
    status: 'SUCCESS',
    signature_valid: true,
    hash_valid: true,
    replay_detected: false,
    nonce: crypto.randomUUID(),
    signature: `DEMO_RSA_SIGNATURE_${id}`,
    hash: `SHA256_DEMO_HASH_${id}`
  };
  state.balance -= amount;
  state.transactions.unshift(tx);
  saveMock(state);
  return { transaction_id: id, status: 'SUCCESS', message: 'Transfer successful', ...tx };
}

export async function getTransactions() {
  if (!USE_MOCK) return (await client.get('/transactions')).data;
  await delay();
  return { transactions: loadMock().transactions };
}

export async function getTransaction(id) {
  if (!USE_MOCK) return (await client.get(`/transactions/${encodeURIComponent(id)}`)).data;
  await delay();
  const tx = loadMock().transactions.find((item) => item.transaction_id === id);
  if (!tx) throw new Error('Transaction not found.');
  return tx;
}

export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem('token'));
}
