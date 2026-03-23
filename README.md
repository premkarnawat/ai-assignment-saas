# ✍️ AI Handwritten Assignment Generator

> Generate 95% realistic handwritten notebook PDFs using AI.
> Students enter a question → AI writes a structured answer → converts to realistic handwritten PDF.

---

## 🧠 Before You Read — Understand These 3 Things

### 1. What is Celery? (Plain English Explanation)

Think of a restaurant:

- You (the **user**) place an order at the counter (**FastAPI server**)
- The counter gives you a token number **immediately** — it doesn't make you wait
- The **kitchen** (**Celery worker**) prepares your food in the background
- When ready, you collect it using your token number

**That's exactly what Celery does in this app:**

```
User clicks "Generate"
   │
   ▼
FastAPI receives request
   │── Returns job_id in 50ms (instantly)
   │── Saves job to database with status = "pending"
   │
   ▼
Celery worker picks up job from Redis queue
   │── Calls Groq AI API (generates structured answer)
   │── Runs handwriting renderer (Pillow image processing)
   │── Builds PDF (ReportLab)
   │── Uploads PDF to Cloudinary
   │── Updates database: status = "done", pdf_url = "..."
   │
   ▼
Frontend polls GET /assignments/{id}/status every 2 seconds
   └── Gets pdf_url when done → shows download button
```

**Why not just do it synchronously (without Celery)?**
- AI call alone takes 3–8 seconds
- Handwriting rendering takes 5–15 seconds
- Total: 8–23 seconds per request
- If 50 users generate at once → server crashes
- Celery handles 1000 jobs simultaneously without breaking

**Celery needs Redis** — Redis is the "bulletin board" where FastAPI posts jobs and Celery reads them.

---

### 2. Docker vs Native on Render — What to Use

**You do NOT need Docker to deploy on Render.**

Render supports **Native Python** — just push your code, and Render installs requirements and runs it. Much simpler.

| | Native (Recommended) | Docker |
|---|---|---|
| Setup complexity | Easy | Moderate |
| Build time | Fast | Slow |
| Debugging | Easier | Harder |
| Use case | Most apps | Complex environments |

**This project uses Native Python on Render.**

Docker files are included for **local development only** (so you can run postgres + redis locally without installing them).

---

### 3. Which Payment Provider to Use — Razorpay

**Use Razorpay. Not Stripe.**

| Feature | Razorpay | Stripe |
|---|---|---|
| Works in India | ✅ Yes | ❌ Needs US/UK entity |
| UPI payments | ✅ Yes | ❌ No |
| Net banking | ✅ Yes | ❌ No |
| Debit cards (India) | ✅ Yes | ⚠️ Limited |
| Student-friendly | ✅ Best | ❌ Most students lack intl cards |
| Free test mode | ✅ Yes | ✅ Yes |
| KYC to go live | Required | Required |

Since this targets Indian students, Razorpay is the obvious choice.
Get free test keys at: https://dashboard.razorpay.com

---

## 🗺️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    STUDENT'S BROWSER                     │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────┐
│              VERCEL (Frontend)                           │
│         Next.js 14 + TypeScript + TailwindCSS            │
│   Landing / Dashboard / Generate / Preview / Pricing    │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API calls
                           ▼
┌─────────────────────────────────────────────────────────┐
│            RENDER.COM (Backend — Web Service)            │
│                     FastAPI (Python)                     │
│         Auth / Assignments / Notebook / OCR / Payments  │
└────────┬─────────────────┬───────────────┬──────────────┘
         │                 │               │
         ▼                 ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Neon Postgres│  │Upstash Redis │  │  Groq API        │
│  (Database)  │  │  (Job Queue) │  │  LLaMA3-70B      │
│   FREE tier  │  │  FREE tier   │  │  (AI answers)    │
└──────────────┘  └──────┬───────┘  └──────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│          RENDER.COM (Celery — Background Worker)         │
│      Picks up jobs → AI → Handwriting → PDF → Upload    │
└──────────────────────────┬──────────────────────────────┘
                           │ Upload PDF
                           ▼
┌─────────────────────────────────────────────────────────┐
│              CLOUDINARY (File Storage)                │
│         Generated PDFs served via public CDN URL         │
│                    10 GB FREE                            │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure Explained

```
ai-assignment-saas/
│
├── README.md                          ← This file
│
├── 📂 frontend/                       ← Deploy to Vercel
│   ├── app/
│   │   ├── page.tsx                   ← Landing page (hero + features + pricing)
│   │   ├── layout.tsx                 ← Root layout with fonts + providers
│   │   ├── globals.css                ← Tailwind + custom styles
│   │   ├── providers.tsx              ← React Query provider
│   │   ├── login/page.tsx             ← Login with email/password
│   │   ├── register/page.tsx          ← Create account
│   │   ├── dashboard/page.tsx         ← View all assignments, stats
│   │   ├── generate/page.tsx          ← Main product page (question → PDF)
│   │   ├── preview/[id]/page.tsx      ← View/download generated PDF
│   │   └── pricing/page.tsx           ← Plans + Razorpay payment flow
│   ├── lib/
│   │   ├── api.ts                     ← All API calls (axios) + polling helper
│   │   └── store.ts                   ← Auth state management (Zustand)
│   ├── .env.example                   ← Copy to .env.local
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
│
├── 📂 backend/                        ← Deploy to Render (Web Service)
│   ├── main.py                        ← FastAPI app, includes all routers
│   ├── requirements.txt               ← All Python packages
│   ├── render.yaml                    ← Render auto-deploy config
│   ├── alembic.ini                    ← Database migration config
│   ├── .env.example                   ← Copy to .env (fill in your keys)
│   │
│   ├── core/
│   │   ├── config.py                  ← Reads all env vars with pydantic-settings
│   │   ├── database.py                ← Async PostgreSQL engine + session
│   │   └── security.py                ← JWT create/verify + password hash
│   │
│   ├── models/                        ← SQLAlchemy database tables
│   │   ├── user.py                    ← users table
│   │   ├── assignment.py              ← assignments table
│   │   ├── payment.py                 ← payments table
│   │   └── usage.py                   ← usage_logs table (rate limiting)
│   │
│   ├── api/routes/
│   │   ├── auth.py                    ← POST /register /login /google /refresh
│   │   ├── assignments.py             ← POST /generate GET /status GET / DELETE
│   │   ├── notebook.py                ← POST /notebook/generate (Pro feature)
│   │   ├── ocr.py                     ← POST /ocr/extract (image → text)
│   │   ├── payments.py                ← Razorpay create-order + verify
│   │   └── users.py                   ← GET /me GET /me/stats
│   │
│   ├── services/
│   │   ├── ai_service.py              ← Calls Groq API, returns structured JSON
│   │   ├── pdf_service.py             ← Orchestrates handwriting → PDF pipeline
│   │   ├── storage_service.py         ← Upload/download from Cloudinary
│   │   └── ocr_service.py             ← Tesseract OCR (image → text)
│   │
│   ├── workers/
│   │   ├── celery_app.py              ← Celery configuration (broker, queues)
│   │   └── tasks.py                   ← process_assignment + process_notebook tasks
│   │
│   ├── scripts/
│   │   └── seed.py                    ← Creates demo user in database
│   │
│   └── tests/
│       └── test_api.py                ← Pytest tests for API endpoints
│
├── 📂 handwriting-engine/             ← The core product differentiator
│   ├── handwriting_renderer.py        ← 7-layer rendering: fonts + variation
│   │                                    + ink simulation + line snapping
│   │                                    + imperfections + page composition
│   └── test_render.py                 ← Run locally to test handwriting output
│
├── 📂 database/
│   └── schema.sql                     ← Full SQL: tables + indexes + triggers
│
├── 📂 deployment/
│   ├── docker-compose.yml             ← LOCAL DEV ONLY: postgres + redis
│   ├── Dockerfile.backend             ← Optional: use if Render Docker selected
│   └── Dockerfile.frontend            ← Optional: Vercel doesn't need this
│
└── 📂 scripts/
    └── install_fonts.sh               ← Downloads Google handwriting fonts
```

---

## 🛠️ Local Development Setup

### Step 1 — Clone repository

```bash
git clone https://github.com/yourname/ai-assignment-saas
cd ai-assignment-saas
```

### Step 2 — Start local database and Redis (Docker required only here)

```bash
cd deployment
docker-compose up -d postgres redis
# This starts PostgreSQL on port 5432 and Redis on port 6379 locally
# Takes about 10 seconds to be ready
```

If you don't want Docker locally, use Neon + Upstash URLs directly in .env.

### Step 3 — Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system tools
# macOS:
brew install tesseract

# Ubuntu/Debian:
sudo apt-get install -y tesseract-ocr libcairo2-dev fonts-freefont-ttf
```

### Step 4 — Environment variables (backend)

```bash
cp .env.example .env
# Edit .env with your API keys (see full reference below)
```

### Step 5 — Database setup

```bash
# Create tables
alembic upgrade head

# Seed test users
python scripts/seed.py
# Creates: demo@writeai.com / demo1234 (Pro user)
#          admin@writeai.com / admin1234
```

### Step 6 — Install handwriting fonts

```bash
cd ..  # go back to project root
bash scripts/install_fonts.sh
```

### Step 7 — Run all three processes (3 terminals)

```bash
# Terminal 1: FastAPI server
cd backend && source venv/bin/activate
uvicorn main:app --reload --port 8000
# Visit: http://localhost:8000/docs

# Terminal 2: Celery worker
cd backend && source venv/bin/activate
celery -A workers.celery_app worker --loglevel=info

# Terminal 3: Next.js frontend
cd frontend
cp .env.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
# Visit: http://localhost:3000
```

### Step 8 — Test the handwriting engine

```bash
cd handwriting-engine
python test_render.py
# Creates test_output.png — open it to see the handwriting
```

---

## ☁️ Production Deployment

### Deploy Backend to Render.com

**Important: Render needs a render.yaml file for one-click deploy.**

1. **Push to GitHub:**
```bash
git add . && git commit -m "ready to deploy" && git push
```

2. **Go to render.com → New → Web Service**

3. **Connect GitHub repository**

4. **Fill in settings:**

| Field | Value |
|---|---|
| Name | `ai-assignment-backend` |
| Root Directory | `backend` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt && alembic upgrade head` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Plan | Free (dev) or Starter — $7/mo (prod) |

5. **Add Environment Variables** (click Advanced → Environment):

```
DATABASE_URL          = postgresql+asyncpg://your_neon_url
REDIS_URL             = rediss://your_upstash_url
CELERY_BROKER_URL     = rediss://your_upstash_url
CELERY_RESULT_BACKEND = rediss://your_upstash_url
GROQ_API_KEY          = gsk_xxx
JWT_SECRET            = any-32-char-random-string
CLOUDINARY_CLOUD_NAME = your_cloud_name
CLOUDINARY_API_KEY    = your_api_key
CLOUDINARY_API_SECRET = your_api_secret
RAZORPAY_KEY_ID       = rzp_test_xxx
RAZORPAY_KEY_SECRET   = xxx
FRONTEND_URL          = https://your-app.vercel.app
ALLOWED_ORIGINS       = ["https://your-app.vercel.app"]
```

6. **Click Deploy** — takes ~3 minutes

7. **Your backend URL:** `https://ai-assignment-backend.onrender.com`

8. **Test it:** Visit `https://ai-assignment-backend.onrender.com/docs`

---

**Deploy Celery Worker to Render:**

1. New → **Background Worker** (not Web Service)
2. Same GitHub repo, same settings
3. **Start Command:** `celery -A workers.celery_app worker --loglevel=info`
4. Same environment variables
5. Deploy

---

### Deploy Frontend to Vercel

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Follow prompts:
# Project name: ai-assignment-frontend
# Framework: Next.js (auto-detected)
# Build settings: leave default
```

**Set environment variables in Vercel dashboard:**
→ vercel.com → project → Settings → Environment Variables

```
NEXT_PUBLIC_API_URL       = https://ai-assignment-backend.onrender.com
NEXT_PUBLIC_RAZORPAY_KEY  = rzp_test_your_key
```

**Redeploy:**
```bash
vercel --prod
```

**Your frontend URL:** `https://ai-assignment-frontend.vercel.app`

---

## 💳 Razorpay Integration Guide

### How the payment flow works

```
1. User clicks "Upgrade to Pro" on /pricing
2. Frontend calls: POST /api/v1/payments/create-order
3. Backend calls Razorpay API → creates order → gets order_id
4. Frontend opens Razorpay popup with order_id
5. User pays (UPI / card / netbanking / wallet)
6. Razorpay calls: POST /api/v1/payments/razorpay-verify
7. Backend verifies HMAC signature (security check)
8. Backend upgrades user.tier = "pro"
9. User can now generate unlimited assignments
```

### Test cards for Razorpay

```
Card number:  4111 1111 1111 1111
Expiry:       Any future date (e.g. 12/26)
CVV:          Any 3 digits
OTP:          1234

Test UPI:     success@razorpay
Test UPI fail: failure@razorpay
```

### Going live with Razorpay

1. Razorpay Dashboard → Account & Settings → Business Profile
2. Upload KYC documents (takes 2-3 working days)
3. Once approved, switch from `rzp_test_...` to `rzp_live_...` keys
4. Update keys in Render and Vercel environment variables

---

## 🔑 Complete Environment Variables Reference

### backend/.env

```env
# ─── Database ───────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
# Get from: https://neon.tech → your project → Connect

# ─── Redis (Celery message queue) ───────────────────────
REDIS_URL=rediss://default:password@region.upstash.io:6379
CELERY_BROKER_URL=rediss://default:password@region.upstash.io:6379
CELERY_RESULT_BACKEND=rediss://default:password@region.upstash.io:6379
# Get from: https://upstash.com → your database → Details
# Note: rediss:// with double 's' = SSL (required for Upstash)

# ─── AI ─────────────────────────────────────────────────
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
# Get from: https://console.groq.com → API Keys

# Optional fallback AI (if Groq fails)
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# ─── Security ───────────────────────────────────────────
JWT_SECRET=make-this-32-characters-long-random
# Generate: python -c "import secrets; print(secrets.token_hex(16))"

JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# ─── File Storage (Cloudinary) ──────────────────────────
# Get all three from: cloudinary.com → Dashboard → API Keys
# Free: 25 GB storage + 25 GB bandwidth/month
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# ─── Payments ────────────────────────────────────────────
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxx
# Get from: https://dashboard.razorpay.com → Settings → API Keys

# ─── App ─────────────────────────────────────────────────
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=["http://localhost:3000"]
# Change to Vercel URL in production

DEBUG=false
FREE_DAILY_LIMIT=3
```

### frontend/.env.local

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
# Change to: https://ai-assignment-backend.onrender.com in production

NEXT_PUBLIC_RAZORPAY_KEY=rzp_test_xxxxxxxxxxxx
# Get from: https://dashboard.razorpay.com → Settings → API Keys
```

---

## 🆓 Free Tier Limits

| Service | Free Limit | What happens when exceeded |
|---|---|---|
| Render Web Service | Sleeps after 15 min idle | First request slow (30s wake-up) |
| Render Background Worker | 750 hrs/month | Worker stops → jobs queue up |
| Neon PostgreSQL | 0.5 GB, 1 project | Pause after limit |
| Upstash Redis | 10,000 cmds/day | Jobs start failing |
| Cloudinary | 25 GB storage + 25 GB bandwidth free | Upgrade at $89/mo |
| Vercel | Unlimited bandwidth | Team features cost $20/mo |
| Groq API | 30 req/min | Auto-retry or OpenAI fallback |

**Cost for 0–200 users/day: $0/month**
**Cost for 200–1000 users/day: ~$17/month** (Render Starter + Upstash Pro)

---

## 🐛 Troubleshooting

### Backend won't start on Render
```
Error: Cannot import 'core.config'
Fix: Make sure Root Directory is set to "backend" in Render settings
```

### Celery can't connect to Redis
```
Error: ConnectionError to Redis
Fix: REDIS_URL must start with rediss:// (not redis://) for Upstash SSL
     Copy the exact URL from Upstash dashboard
```

### CORS error in browser
```
Error: Access to XMLHttpRequest blocked by CORS policy
Fix: Add your Vercel URL exactly to ALLOWED_ORIGINS in Render env:
     ALLOWED_ORIGINS=["https://your-exact-domain.vercel.app"]
```

### Render backend is slow to respond
```
This is normal on free tier — it sleeps after 15 minutes
First request wakes it up (takes 20-30 seconds)
Fix: Add a cron job to ping /health every 10 minutes
     Or upgrade to Starter plan ($7/mo) for always-on
```

### PDF generation fails
```
Error in handwriting renderer: font not found
Fix: Run bash scripts/install_fonts.sh
     On Render: add to build command: apt-get install -y fonts-freefont-ttf
```

### Razorpay popup not opening
```
Check: NEXT_PUBLIC_RAZORPAY_KEY is set in Vercel env variables
Check: You're using rzp_test_... keys (not rzp_live_... in test)
Check: Browser console for JavaScript errors
```

---

## 🧪 Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v

# Expected output:
# test_health PASSED
# test_register PASSED
# test_login PASSED
# test_wrong_password PASSED
```

---

## 📈 Scaling Beyond Free Tier

When you have 1000+ users:

1. **Render Starter** ($7/mo) — No sleep, always-on
2. **Upstash Pro** ($10/mo) — 1M Redis commands/day
3. **Neon Pro** ($19/mo) — 10 GB storage
4. Add **Render autoscaling** — multiple backend instances
5. Cloudinary already serves files via global CDN — no extra setup

---

## 🔗 All Service Links

| Service | URL | What it's for |
|---|---|---|
| Groq | https://console.groq.com | Free AI API keys |
| Neon | https://neon.tech | Serverless PostgreSQL |
| Upstash | https://upstash.com | Serverless Redis |
| Cloudinary | https://cloudinary.com | PDF file storage |
| Razorpay | https://dashboard.razorpay.com | Payments |
| Render | https://render.com | Backend hosting |
| Vercel | https://vercel.com | Frontend hosting |
| API Docs | http://localhost:8000/docs | Swagger (local) |
