from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from datetime import datetime
import secrets
import hashlib
from typing import List, Optional
import uuid

from shared.core.database import get_db
from shared.core.models import ApiKey

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])
# Authenticated endpoints (assuming auth is handled globally or we need to add depends)
# For now, assuming internal dashboard usage implies checked auth or open for dev (based on user context).
# Ideally, we should add user auth dependency here if the app has it.

class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class ApiKeyGenerated(ApiKeyResponse):
    key: str # Only returned once

@router.post("", response_model=ApiKeyGenerated)
async def create_api_key(data: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    # Generate secure key
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:8]
    
    new_key = ApiKey(
        key_hash=key_hash,
        name=data.name,
        prefix=prefix,
        is_active=True
    )
    
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    # Manually construct response to include the raw key
    return ApiKeyGenerated(
        id=new_key.id,
        name=new_key.name,
        prefix=new_key.prefix,
        created_at=new_key.created_at,
        is_active=new_key.is_active,
        key=raw_key
    )

@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    query = select(ApiKey).where(ApiKey.is_active == True).order_by(ApiKey.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    query = delete(ApiKey).where(ApiKey.id == id)
    await db.execute(query)
    await db.commit()
