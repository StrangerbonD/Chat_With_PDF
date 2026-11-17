"""
Authentication routes for Chat with PDF API.
Prefix: /api/auth
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db, User, RefreshToken, VerificationCode
from app.deps import get_current_user
from app.email import send_email
from app.security import (
    hash_password,
    verify_password,
    generate_code,
    hash_code,
    generate_token_id,
    create_access_token,
    create_refresh_token,
    decode_token,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["auth"])

_PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d).+$"
_COOKIE_NAME = "refresh_token"
_COOKIE_PATH = "/api/auth"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        import re
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.match(_PASSWORD_REGEX, v):
            raise ValueError(
                "Password must contain at least one letter and one digit"
            )
        return v


class VerifyEmailBody(BaseModel):
    email: EmailStr
    code: str


class ResendCodeBody(BaseModel):
    email: EmailStr
    purpose: str = "verify_email"


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    email: EmailStr
    code: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        import re
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.match(_PASSWORD_REGEX, v):
            raise ValueError(
                "Password must contain at least one letter and one digit"
            )
        return v


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _set_refresh_cookie(response: Response, token: str, max_age: int) -> None:
    s = get_settings()
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=s.is_cookie_secure,
        path=_COOKIE_PATH,
        max_age=max_age,
    )


def _clear_refresh_cookie(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(
        key=_COOKIE_NAME,
        path=_COOKIE_PATH,
        httponly=True,
        samesite="lax",
        secure=s.is_cookie_secure,
    )


async def _get_user_by_email(
    db: AsyncSession, email: str
) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_latest_verification_code(
    db: AsyncSession, user_id: str, purpose: str, include_used: bool = False
) -> Optional[VerificationCode]:
    """Return the most-recent non-expired code for a user/purpose."""
    q = select(VerificationCode).where(
        VerificationCode.user_id == user_id,
        VerificationCode.purpose == purpose,
    )
    if not include_used:
        q = q.where(VerificationCode.used == False)  # noqa: E712
    q = q.order_by(VerificationCode.created_at.desc())
    result = await db.execute(q)
    vc = result.scalar_one_or_none()
    if vc and _to_utc(vc.expires_at) > _now():
        return vc
    return None


async def _revoke_all_refresh_tokens(db: AsyncSession, user_id: str) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)  # noqa: E712
        .values(revoked=True)
    )


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterBody, db: AsyncSession = Depends(get_db)):
    email = body.email.lower().strip()

    existing = await _get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    import uuid as _uuid
    user = User(
        id=str(_uuid.uuid4()),
        email=email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name.strip(),
        is_verified=False,
    )
    db.add(user)
    await db.flush()  # populate user.id before creating child rows

    code = generate_code()
    code_hash = hash_code(code)
    verification = VerificationCode(
        id=str(_uuid.uuid4()),
        user_id=user.id,
        code_hash=code_hash,
        purpose="verify_email",
        expires_at=_now() + timedelta(minutes=10),
    )
    db.add(verification)
    await db.commit()

    await send_email(
        to=email,
        subject="Verify your email",
        body=f"Your verification code is: {code}\n\nIt expires in 10 minutes.",
    )

    return {"message": "Check your email for the verification code", "code": code}


# ---------------------------------------------------------------------------
# POST /verify-email
# ---------------------------------------------------------------------------

@router.post("/verify-email")
async def verify_email(body: VerifyEmailBody, db: AsyncSession = Depends(get_db)):
    email = body.email.lower().strip()

    user = await _get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid code")

    vc = await _get_latest_verification_code(db, user.id, "verify_email")
    if not vc:
        raise HTTPException(status_code=400, detail="Invalid code")

    # Increment attempt count first
    vc.attempts += 1

    if vc.attempts > 5:
        vc.used = True
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid code")

    if vc.code_hash != hash_code(body.code):
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid code")

    # Correct code
    vc.used = True
    user.is_verified = True
    await db.commit()

    return {"message": "Email verified"}


# ---------------------------------------------------------------------------
# POST /resend-code
# ---------------------------------------------------------------------------

@router.post("/resend-code")
async def resend_code(body: ResendCodeBody, db: AsyncSession = Depends(get_db)):
    import uuid as _uuid

    email = body.email.lower().strip()
    _success_msg = {"message": "Code sent if account exists"}

    user = await _get_user_by_email(db, email)
    if not user:
        return _success_msg

    # Check rate limit: last code for this purpose
    q = (
        select(VerificationCode)
        .where(
            VerificationCode.user_id == user.id,
            VerificationCode.purpose == body.purpose,
        )
        .order_by(VerificationCode.created_at.desc())
    )
    result = await db.execute(q)
    last_code = result.scalar_one_or_none()

    if last_code and _to_utc(last_code.created_at) > _now() - timedelta(seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Wait before resending",
        )

    code = generate_code()
    code_hash = hash_code(code)
    vc = VerificationCode(
        id=str(_uuid.uuid4()),
        user_id=user.id,
        code_hash=code_hash,
        purpose=body.purpose,
        expires_at=_now() + timedelta(minutes=10),
    )
    db.add(vc)
    await db.commit()

    subject_map = {
        "verify_email": "Your verification code",
        "reset_password": "Your password reset code",
    }
    subject = subject_map.get(body.purpose, "Your code")
    await send_email(
        to=email,
        subject=subject,
        body=f"Your code is: {code}\n\nIt expires in 10 minutes.",
    )

    return {"message": "Code sent if account exists", "code": code}


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post("/login")
async def login(
    body: LoginBody,
    response: Response,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid

    email = body.email.lower().strip()

    user = await _get_user_by_email(db, email)

    # Brute-force protection: 5 failed attempts locks for 5 minutes
    if user:
        if (
            user.failed_login_attempts >= 5
            and user.last_failed_login
            and _to_utc(user.last_failed_login) > _now() - timedelta(minutes=5)
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Try again later.",
            )

    if not user or not verify_password(body.password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            user.last_failed_login = _now()
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Reset failed attempts counter on success
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.last_failed_login = None
        await db.commit()

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email first",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated",
        )

    access_token = create_access_token(user.id, user.role)
    jti = generate_token_id()
    refresh_token = create_refresh_token(user.id, user.role, jti=jti)

    token_hash = _sha256(refresh_token)
    expires_at = _now() + timedelta(days=settings.refresh_token_days)
    rt = RefreshToken(
        id=str(_uuid.uuid4()),
        jti=jti,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(rt)
    await db.commit()

    max_age = settings.refresh_token_days * 24 * 3600
    _set_refresh_cookie(response, refresh_token, max_age)

    # Send login alert email to the user
    login_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    user_name = user.full_name or "User"
    email_body = (
        f"Hello {user_name},\n\n"
        f"A new login to your Chat with PDF account was detected.\n\n"
        f"Account: {user.email}\n"
        f"Time: {login_time}\n\n"
        f"If this was you, you can safely ignore this notification.\n"
        f"If you did not initiate this login, please reset your password immediately.\n\n"
        f"Best regards,\n"
        f"Bondhon Das (bondhondas16@gmail.com)\n"
        f"Chat with PDF"
    )
    background_tasks.add_task(
        send_email,
        to=user.email,
        subject="Security Notification: Successful Login to Chat with PDF",
        body=email_body,
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------

@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    import uuid as _uuid

    raw_token = request.cookies.get(_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(raw_token, expected_type="refresh")
    except HTTPException:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    jti = payload.get("jti")
    user_id = payload.get("sub")

    # Look up the stored refresh token by jti
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.jti == jti)
    )
    stored: Optional[RefreshToken] = result.scalar_one_or_none()

    if not stored:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    # Reuse detection: if already revoked, invalidate all sessions
    if stored.revoked:
        await _revoke_all_refresh_tokens(db, stored.user_id)
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalidated",
        )

    # Check expiry
    if _to_utc(stored.expires_at) < _now():
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    # Verify token hash matches what's stored
    if _sha256(raw_token) != stored.token_hash:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    # Load user for role
    result2 = await db.execute(select(User).where(User.id == stored.user_id))
    user: Optional[User] = result2.scalar_one_or_none()
    if not user or not user.is_active:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account unavailable")

    # Revoke old token
    stored.revoked = True

    # Issue new tokens
    new_jti = generate_token_id()
    new_access_token = create_access_token(user.id, user.role)
    new_refresh_token = create_refresh_token(user.id, user.role, jti=new_jti)

    new_expires_at = _now() + timedelta(days=settings.refresh_token_days)
    new_rt = RefreshToken(
        id=str(_uuid.uuid4()),
        jti=new_jti,
        user_id=user.id,
        token_hash=_sha256(new_refresh_token),
        expires_at=new_expires_at,
        revoked=False,
    )
    db.add(new_rt)
    await db.commit()

    max_age = settings.refresh_token_days * 24 * 3600
    _set_refresh_cookie(response, new_refresh_token, max_age)

    return {"access_token": new_access_token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw_token = request.cookies.get(_COOKIE_NAME)
    if raw_token:
        try:
            payload = decode_token(raw_token, expected_type="refresh")
            jti = payload.get("jti")
            if jti:
                result = await db.execute(
                    select(RefreshToken).where(
                        RefreshToken.jti == jti,
                        RefreshToken.revoked == False,  # noqa: E712
                    )
                )
                stored = result.scalar_one_or_none()
                if stored:
                    stored.revoked = True
                    await db.commit()
        except Exception:
            pass  # always clear cookie and return 200

    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    }


# ---------------------------------------------------------------------------
# POST /forgot-password
# ---------------------------------------------------------------------------

@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordBody, db: AsyncSession = Depends(get_db)):
    import uuid as _uuid

    email = body.email.lower().strip()
    _msg = {"message": "If the account exists, a reset code was sent"}

    user = await _get_user_by_email(db, email)
    if user and user.is_verified:
        # Rate-limit: 60s cooldown between send attempts
        q = (
            select(VerificationCode)
            .where(
                VerificationCode.user_id == user.id,
                VerificationCode.purpose == "reset_password",
            )
            .order_by(VerificationCode.created_at.desc())
        )
        last_code = (await db.execute(q)).scalar_one_or_none()
        if last_code and _to_utc(last_code.created_at) > _now() - timedelta(seconds=60):
            return _msg

        code = generate_code()
        code_hash = hash_code(code)
        vc = VerificationCode(
            id=str(_uuid.uuid4()),
            user_id=user.id,
            code_hash=code_hash,
            purpose="reset_password",
            expires_at=_now() + timedelta(minutes=10),
        )
        db.add(vc)
        await db.commit()

        await send_email(
            to=email,
            subject="Password reset code",
            body=f"Your password reset code is: {code}\n\nIt expires in 10 minutes.",
        )
        return {"message": "If the account exists, a reset code was sent", "code": code}

    return _msg


# ---------------------------------------------------------------------------
# POST /reset-password
# ---------------------------------------------------------------------------

@router.post("/reset-password")
async def reset_password(body: ResetPasswordBody, db: AsyncSession = Depends(get_db)):
    email = body.email.lower().strip()

    user = await _get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid code")

    vc = await _get_latest_verification_code(db, user.id, "reset_password")
    if not vc:
        raise HTTPException(status_code=400, detail="Invalid code")

    vc.attempts += 1

    if vc.attempts > 5:
        vc.used = True
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid code")

    if vc.code_hash != hash_code(body.code):
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid code")

    # Correct — update password, mark code used, revoke all refresh tokens
    user.hashed_password = hash_password(body.new_password)
    vc.used = True

    await _revoke_all_refresh_tokens(db, user.id)
    await db.commit()

    return {"message": "Password reset successful"}
