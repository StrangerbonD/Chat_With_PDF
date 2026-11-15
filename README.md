# Chat with PDF

A RAG-powered document Q&A app with JWT authentication, built with React + FastAPI + Gemini.

---

## Stack

- **Frontend**: React 18, Vite, Tailwind CSS v4, Axios
- **Backend**: FastAPI, SQLAlchemy (async SQLite), PyJWT, bcrypt
- **AI**: Google Gemini 2.5 Flash (LLM) + gemini-embedding-001 (embeddings)
- **Vector DB**: ChromaDB (persistent, cosine distance)

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Gemini API key (https://aistudio.google.com/app/apikey)
- An SMTP account (Mailtrap or Gmail App Password)

---

### Backend

```bash
cd chat-with-pdf/backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your values
```

**`.env` required fields:**

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | From Google AI Studio |
| `JWT_SECRET` | Long random string (32+ chars) |
| `SMTP_HOST` | e.g. `smtp.mailtrap.io` or `smtp.gmail.com` |
| `SMTP_PORT` | Usually `587` |
| `SMTP_USER` | Your SMTP username |
| `SMTP_PASSWORD` | Your SMTP password / app password |
| `SMTP_FROM` | Sender address |
| `ADMIN_EMAIL` | First admin email (created on startup) |
| `ADMIN_PASSWORD` | First admin password (min 8 chars, 1 letter + 1 number) |

**Gmail App Password setup:**
1. Enable 2FA on your Google account.
2. Go to Google Account → Security → App Passwords.
3. Create one, use `smtp.gmail.com`, port `587`, the generated password.

**Mailtrap setup:**
1. Create a free account at https://mailtrap.io
2. Go to Email Testing → Inboxes → SMTP Settings.
3. Copy HOST, PORT, USERNAME, PASSWORD.

```bash
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

---

### Frontend

```bash
cd chat-with-pdf/frontend
npm install

cp .env.example .env
# VITE_API_URL=http://localhost:8000

npm run dev
# App at http://localhost:5173
```

---

## First Admin

The first admin is created automatically at startup from `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`. No manual step needed. Only created if no admin exists.

---

## API Endpoints

### Auth (`/api/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register (email, password, full_name) |
| POST | `/verify-email` | Verify email with 6-digit code |
| POST | `/resend-code` | Resend verification code (60s cooldown) |
| POST | `/login` | Login → access token + refresh cookie |
| POST | `/refresh` | Rotate refresh token → new access token |
| POST | `/logout` | Revoke refresh token |
| GET | `/me` | Current user info |
| POST | `/forgot-password` | Send password reset code |
| POST | `/reset-password` | Reset password with code |

### Documents (`/api/documents`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload PDF (multipart, max 20MB, 200 pages) |
| GET | `/` | List your documents |
| DELETE | `/{document_id}` | Delete document and its chunks |

### Chat (`/api/chat`)

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/` | `{document_id, question}` | Ask a question about a document |

### Admin (`/api/admin`) — admin role required

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | Paginated user list with search |
| GET | `/users/{id}` | User detail |
| PATCH | `/users/{id}` | Update is_active / role |
| DELETE | `/users/{id}` | Delete user and all their data |
| GET | `/stats` | Platform stats |

### Health

| Method | Endpoint |
|--------|----------|
| GET | `/api/health` |

---

## Testing

### Manual flow

1. **Register**: POST `/api/auth/register` with email, password, full_name.
2. **Verify**: Check email for 6-digit code → POST `/api/auth/verify-email`.
3. **Login**: POST `/api/auth/login` → copy `access_token`.
4. **Upload**: POST `/api/documents/upload` with Authorization header and a PDF file.
5. **Chat**: POST `/api/chat` with `{document_id, question}`.
6. **Refresh**: POST `/api/auth/refresh` (uses httpOnly cookie automatically).
7. **Forgot password**: POST `/api/auth/forgot-password`, then `/reset-password`.
8. **Admin**: Log in as admin, visit `/admin` in the UI.

### Using the Swagger UI

Visit `http://localhost:8000/docs`. Use the Authorize button with `Bearer <access_token>`.

---

## Security Notes

- Passwords hashed with bcrypt (72-byte input limit handled).
- Refresh tokens stored as SHA-256 hashes; rotation on every use.
- Revoked token reuse invalidates all user sessions.
- Access token in React memory only (never localStorage).
- CORS limited to `FRONTEND_ORIGIN`.
- Refresh cookie: httpOnly, SameSite=Lax, path=/api/auth.
- Gemini prompt treats PDF content as data, never instructions.

---

## Project Structure

```
chat-with-pdf/
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── components/
│       │   ├── ChatWindow.jsx
│       │   ├── ChatInput.jsx
│       │   ├── PdfUploader.jsx
│       │   └── ProtectedRoute.jsx   (exports ProtectedRoute & AdminRoute)
│       ├── pages/
│       │   ├── Login.jsx
│       │   ├── Register.jsx
│       │   ├── VerifyEmail.jsx
│       │   ├── ForgotPassword.jsx
│       │   ├── ResetPassword.jsx
│       │   ├── Chat.jsx
│       │   └── Admin.jsx
│       ├── context/
│       │   └── AuthContext.jsx
│       ├── services/
│       │   └── api.js
│       ├── App.jsx
│       ├── main.jsx
│       └── index.css
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py        # engine, session, ORM models
│   │   ├── security.py        # password hashing, JWT, code generation
│   │   ├── email.py           # send_email (aiosmtplib)
│   │   ├── deps.py            # get_current_user, require_admin
│   │   ├── routes_auth.py     # register, verify, login, refresh, logout, reset
│   │   ├── routes_admin.py    # users, roles, stats
│   │   ├── routes.py          # documents + chat + health
│   │   ├── pdf_processor.py   # PyMuPDF, secure temp files, chunking
│   │   ├── rag.py             # Gemini embeddings & LLM answering
│   │   └── vector_store.py    # ChromaDB PersistentClient
│   ├── .env.example
│   └── requirements.txt
├── .gitignore
└── README.md
```
