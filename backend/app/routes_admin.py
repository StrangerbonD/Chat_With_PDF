from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional

from app.database import get_db, User, Document, RefreshToken, VerificationCode
from app.deps import require_admin, get_current_user
from app.vector_store import delete_document_chunks

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Pydantic schemas ────────────────────────────────────────────────────────

class UserPatchBody(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None


# ── Helpers ─────────────────────────────────────────────────────────────────

async def _doc_count_for(user_id: str, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(Document).where(Document.user_id == user_id)
    )
    return result.scalar_one()


def _user_dict(user: User, document_count: int) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "document_count": document_count,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = select(User)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            User.email.ilike(pattern) | User.full_name.ilike(pattern)
        )

    # Total count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    users = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()

    users_out = []
    for u in users:
        dc = await _doc_count_for(u.id, db)
        users_out.append(_user_dict(u, dc))

    return {"total": total, "users": users_out}


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    dc = await _doc_count_for(user_id, db)
    return _user_dict(user, dc)


@router.patch("/users/{user_id}")
async def patch_user(
    user_id: str,
    body: UserPatchBody,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(400, "Cannot modify your own account")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    if body.is_active is not None:
        user.is_active = body.is_active
        # If deactivating, revoke all refresh tokens
        if not body.is_active:
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
                .values(revoked=True)
            )

    if body.role is not None:
        user.role = body.role

    await db.commit()
    await db.refresh(user)
    dc = await _doc_count_for(user_id, db)
    return _user_dict(user, dc)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(400, "Cannot delete your own account")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    # Delete Chroma chunks for each document
    docs = (await db.execute(select(Document).where(Document.user_id == user_id))).scalars().all()
    for doc in docs:
        delete_document_chunks(doc.id)

    # Delete DB rows in dependency order
    await db.execute(delete(Document).where(Document.user_id == user_id))
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await db.execute(delete(VerificationCode).where(VerificationCode.user_id == user_id))
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    verified_users = (
        await db.execute(select(func.count()).select_from(User).where(User.is_verified == True))
    ).scalar_one()
    active_users = (
        await db.execute(select(func.count()).select_from(User).where(User.is_active == True))
    ).scalar_one()
    total_documents = (await db.execute(select(func.count()).select_from(Document))).scalar_one()

    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "active_users": active_users,
        "total_documents": total_documents,
    }
