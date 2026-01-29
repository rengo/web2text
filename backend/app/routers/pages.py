from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from shared.core import models, schemas, database

router = APIRouter(prefix="/pages", tags=["pages"])

@router.get("/", response_model=List[schemas.PageRead])
async def read_pages(
    site_id: Optional[UUID] = None,
    status: Optional[models.PageStatus] = None,
    discovered_via: Optional[models.DiscoverySource] = None,
    published_from: Optional[datetime] = None,
    published_to: Optional[datetime] = None,
    q: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(database.get_db)
):
    query = select(models.Page)
    
    if site_id:
        query = query.where(models.Page.site_id == site_id)
    if status:
        query = query.where(models.Page.status == status)
    if discovered_via:
        query = query.where(models.Page.discovered_via == discovered_via)
    if published_from:
        query = query.where(models.Page.published_at >= published_from)
    if published_to:
        query = query.where(models.Page.published_at <= published_to)
    if q:
        query = query.where(models.Page.title.ilike(f"%{q}%"))
        
    query = query.order_by(desc(models.Page.published_at)).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{page_id}", response_model=schemas.PageDetail)
async def read_page_detail(page_id: UUID, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Page).where(models.Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Fetch latest content
    content_result = await db.execute(
        select(models.PageContent)
        .where(models.PageContent.page_id == page_id)
        .order_by(desc(models.PageContent.created_at))
        .limit(1)
    )
    latest_content = content_result.scalar_one_or_none()
    
    page_detail = schemas.PageDetail.from_orm(page)
    if latest_content:
        page_detail.latest_content = schemas.PageContentRead.from_orm(latest_content)
        
    return page_detail
