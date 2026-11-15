import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_tables, engine, AsyncSessionLocal, User
from app.security import hash_password
from app.routes_auth import router as auth_router
from app.routes_admin import router as admin_router
from app.routes import router as main_router
from sqlalchemy import select
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_startup():
    settings = get_settings()
    missing = []
    if not settings.gemini_api_key:
        missing.append("GEMINI_API_KEY")
    if not settings.jwt_secret:
        missing.append("JWT_SECRET")
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


async def seed_admin():
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role == "admin")
        )
        existing_admin = result.scalar_one_or_none()
        if existing_admin:
            return
        admin = User(
            id=str(uuid.uuid4()),
            email=settings.admin_email.lower().strip(),
            hashed_password=hash_password(settings.admin_password),
            full_name="Admin",
            role="admin",
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        logger.info(f"Admin user created: {settings.admin_email}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup()
    await create_tables(engine)
    await seed_admin()
    yield


settings = get_settings()

app = FastAPI(title="Chat with PDF", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(main_router)
