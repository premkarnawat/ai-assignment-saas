# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from core.config import settings
from core.database import engine, Base
from api.routes import auth, assignments, notebook, ocr, payments, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="AI Assignment Generator API",
    description="Production API for AI-powered handwritten assignment generation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router,        prefix="/api/v1/auth",        tags=["Authentication"])
app.include_router(assignments.router, prefix="/api/v1/assignments",  tags=["Assignments"])
app.include_router(notebook.router,    prefix="/api/v1/notebook",     tags=["Notebook Generator"])
app.include_router(ocr.router,         prefix="/api/v1/ocr",          tags=["OCR"])
app.include_router(payments.router,    prefix="/api/v1/payments",     tags=["Payments"])
app.include_router(users.router,       prefix="/api/v1/users",        tags=["Users"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
