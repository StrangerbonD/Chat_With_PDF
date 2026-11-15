# Chat with PDF

A production-grade Document Q&A application powered by Google Gemini RAG (Retrieval-Augmented Generation) and FastAPI with JWT authentication and an Admin management panel.

---

## Overview

Chat with PDF allows users to upload documents in PDF format and ask questions in natural English. Answers are grounded exclusively in the uploaded document context using Google Gemini embeddings and LLM reasoning, returning exact source page citations for every response.

Key characteristics:
- English-only processing: Document text extraction, vector embeddings, context generation, and assistant responses are strictly in English.
- No hallucinations: If requested information is absent from the uploaded document, the system explicitly reports that the document contains insufficient information.
- Multi-tenant isolation: Documents, vector embeddings, and chat histories are isolated by user ID at database and vector-store levels.
- Minimal UI design: Pure text and clean contrast interface with dark black and light theme toggle. Zero icon fonts or icon graphics in application UI.

---

## Tech Stack

### Frontend
- Framework: React 18 with Vite
- Styling: Tailwind CSS v4 (Pure Dark Black and Light mode support)
- HTTP Client: Axios with automatic request queuing and token refresh interceptors
- Routing: React Router DOM v7 (Public, Protected, and Admin routes)

### Backend
- Framework: FastAPI (Python 3.11+)
- Data Validation: Pydantic v2 and Pydantic Settings
- Database: SQLAlchemy 2.0 (asyncio) with SQLite (WAL mode enabled)
- Authentication: PyJWT (HS256) access tokens and HTTP-only rotating refresh tokens
- Password Security: bcrypt (explicit 72-byte truncation safe)
- Email / OTP: aiosmtplib with STARTTLS and dev simulator fallback

### AI & Retrieval (RAG)
- Document Processing: PyMuPDF (fitz) with secure temporary file handling and page tracking
- Vector Store: ChromaDB (PersistentClient, cosine distance metric)
- Embeddings: Google Gemini gemini-embedding-001 (batching and exponential backoff retry)
- LLM Answering: Google Gemini gemini-3.5-flash-lite (fast inference, fallback to gemini-3.8-flash)

---

## Project Structure

```
chat-with-pdf/
|-- docker-compose.yml
|-- README.md
|-- .gitignore
|-- backend/
|   |-- Dockerfile
|   |-- .dockerignore
|   |-- .env.example
|   |-- requirements.txt
|   \-- app/
|       |-- __init__.py
|       |-- main.py            # FastAPI entry point, CORS, startup validation, lifespan
|       |-- config.py          # Pydantic Settings and environment configuration
|       |-- database.py        # Async SQLAlchemy engine, models, WAL pragmas
|       |-- deps.py            # Dependency injection: get_current_user, require_admin
|       |-- security.py        # bcrypt hashing, JWT issuance and verification, OTP generator
|       |-- email.py           # aiosmtplib async STARTTLS sender and dev simulator
|       |-- pdf_processor.py   # PyMuPDF parser, chunker (~3000 chars / 500 overlap)
|       |-- rag.py             # Gemini embeddings and grounded generation
|       |-- vector_store.py    # ChromaDB persistent collection and scoped queries
|       |-- routes.py          # Health, PDF upload/delete, RAG chat endpoints
|       |-- routes_auth.py     # Register, verify-email, login, refresh, logout, password reset
|       \-- routes_admin.py    # User listing, pagination, roles, stats, cascade deletion
\-- frontend/
    |-- Dockerfile
    |-- nginx.conf
    |-- .dockerignore
    |-- index.html
    |-- package.json
    |-- vite.config.js
    |-- .env.example
    |-- public/
    |   \-- favicon.svg
    \-- src/
        |-- main.jsx
        |-- App.jsx
        |-- index.css
        |-- components/
        |   |-- ChatInput.jsx
        |   |-- ChatWindow.jsx
        |   |-- PdfUploader.jsx
        |   \-- ProtectedRoute.jsx
        |-- context/
        |   |-- AuthContext.jsx
        |   \-- ThemeContext.jsx
        |-- pages/
        |   |-- Landing.jsx
        |   |-- Login.jsx
        |   |-- Register.jsx
        |   |-- VerifyEmail.jsx
        |   |-- ForgotPassword.jsx
        |   |-- ResetPassword.jsx
        |   |-- Chat.jsx
        |   \-- Admin.jsx
        \-- services/
            \-- api.js
```

---

## Environment Configuration

### Backend (.env)

Create `backend/.env` based on `backend/.env.example`:

| Key | Description | Default / Example |
|---|---|---|
| GEMINI_API_KEY | Google AI Studio API key | Required |
| JWT_SECRET | 32+ character random secret string | Required |
| ENVIRONMENT | Application environment | development / production |
| ACCESS_TOKEN_MINUTES | Access token lifespan | 15 |
| REFRESH_TOKEN_DAYS | Refresh token validity | 7 |
| DATABASE_URL | Async database connection string | sqlite+aiosqlite:///./chat_pdf.db |
| CHROMA_PATH | Persistent directory for ChromaDB | ./chroma_data |
| FRONTEND_ORIGIN | Allowed CORS origins (comma-separated) | http://localhost:5173 |
| COOKIE_SECURE | Secure flag for refresh cookie | false (true in production HTTPS) |
| SMTP_HOST | Outgoing SMTP host | smtp.mailtrap.io |
| SMTP_PORT | Outgoing SMTP port | 587 |
| SMTP_USER | SMTP username | Optional in local dev |
| SMTP_PASSWORD | SMTP password or app password | Optional in local dev |
| SMTP_FROM | Default sender email address | noreply@chatpdf.local |
| ADMIN_EMAIL | Seed administrator email | admin@example.com |
| ADMIN_PASSWORD | Seed administrator password | Admin123456 |
| MAX_FILE_MB | Maximum allowed PDF size in MB | 20 |
| MAX_PAGES | Maximum allowed pages per document | 200 |

### Frontend (.env)

Create `frontend/.env` based on `frontend/.env.example`:

| Key | Description | Default / Example |
|---|---|---|
| VITE_API_URL | Backend base URL | http://localhost:8000 |

---

## Local Development Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and enter your GEMINI_API_KEY and JWT_SECRET

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at:
- API Root: http://localhost:8000
- Swagger Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Start development server
npm run dev
```

The web client will be available at:
- Web App: http://localhost:5173

---

## Production Deployment

### Option A: Docker Compose (Recommended)

1. Ensure Docker and Docker Compose are installed on your host.
2. In `backend/.env`, set your `GEMINI_API_KEY`, strong `JWT_SECRET`, and SMTP details.
3. In `docker-compose.yml`, verify ports and domain configurations.
4. Run the stack:

```bash
docker compose up -d --build
```

To view logs:
```bash
docker compose logs -f
```

To stop containers:
```bash
docker compose down
```

### Option B: Linux VPS / Systemd + Nginx

#### 1. Backend Deployment

Create a systemd service file at `/etc/systemd/system/chatpdf-backend.service`:

```ini
[Unit]
Description=Chat with PDF Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/chat-with-pdf/backend
EnvironmentFile=/var/www/chat-with-pdf/backend/.env
ExecStart=/var/www/chat-with-pdf/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable chatpdf-backend
sudo systemctl start chatpdf-backend
```

#### 2. Frontend Deployment

Build the production assets:
```bash
cd frontend
npm install
npm run build
```

Copy the generated `dist` folder to your web root:
```bash
sudo cp -r dist/* /var/www/chat-with-pdf-client/
```

Configure Nginx reverse proxy at `/etc/nginx/sites-available/chat-with-pdf`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    root /var/www/chat-with-pdf-client;
    index index.html;

    # Single-page application route fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Reverse proxy backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 25M;
}
```

Enable the site and obtain SSL with Certbot:
```bash
sudo ln -s /etc/nginx/sites-available/chat-with-pdf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d yourdomain.com
```

---

## API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description |
|---|---|---|
| POST | /register | Register new user account |
| POST | /verify-email | Validate 6-digit email OTP |
| POST | /resend-code | Resend OTP code (60-second cooldown) |
| POST | /login | Authenticate user, returns access token + set refresh cookie |
| POST | /refresh | Rotate refresh token, issue fresh access token |
| POST | /logout | Invalidate refresh token and clear cookie |
| GET | /me | Retrieve authenticated user profile |
| POST | /forgot-password | Dispatch password recovery OTP |
| POST | /reset-password | Apply new password using OTP verification |

### Document Management (`/api/documents`)

| Method | Endpoint | Description |
|---|---|---|
| POST | /upload | Upload PDF, extract text, chunk and index in ChromaDB |
| GET | / | List uploaded documents for current user |
| DELETE | /{document_id} | Remove document record and its vector chunks |

### RAG Chat (`/api/chat`)

| Method | Endpoint | Description |
|---|---|---|
| POST | / | Submit query against document; returns answer and source pages |

### Administration (`/api/admin`)

| Method | Endpoint | Description |
|---|---|---|
| GET | /users | List users with search and pagination |
| GET | /users/{id} | Retrieve detailed user metadata |
| PATCH | /users/{id} | Update user status (active/deactive) or role |
| DELETE | /{user_id} | Cascade delete user, documents, and vector store data |
| GET | /stats | Summary metrics (users, verified, active, documents) |

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/health | Service availability probe |

---

## Production Readiness Checklist

1. Access Token Security: Stored in memory in React client; never written to localStorage or cookies.
2. Refresh Token Security: Stored in HTTP-only, SameSite=Lax cookie with rotation on every use and automatic family revocation upon reuse detection.
3. Brute Force Protection: Account lockout after 5 consecutive failed login attempts with a 15-minute cooldown.
4. Input Protection: Streaming upload chunk reader with strict 20MB limit preventing server memory exhaustion.
5. SQL Concurrency: SQLite WAL mode with synchronous=NORMAL and 5000ms busy timeout preventing locks under concurrent traffic.
6. RAG Grounding: System prompts strictly forbid external hallucination and enforce explicit insufficient information responses.
7. Error Sanitization: Unhandled server exceptions are caught and sanitized to prevent internal traceback leaks.
