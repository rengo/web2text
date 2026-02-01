from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_, func
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import math

from shared.core import models, schemas, database
from backend.app import auth

router = APIRouter(prefix="/feed", tags=["feed"], dependencies=[Depends(auth.get_current_user)])

@router.get("/new", response_model=schemas.PaginatedFeedResponse)
async def get_new_feed(
    since: datetime,
    site_id: UUID = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Devuelve páginas processed donde (scraped_at > since) o (first_seen_at > since).
    Incluye extracted_text completo.
    """
    # Base conditions
    conditions = [
        models.Page.status == models.PageStatus.PROCESSED,
        or_(
            models.Page.scraped_at > since,
            models.Page.first_seen_at > since
        )
    ]
    
    if site_id:
        conditions.append(models.Page.site_id == site_id)

    # Count query
    count_query = select(func.count(models.Page.id)).join(
        models.Site, models.Page.site_id == models.Site.id
    ).where(*conditions)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Data query
    offset = (page - 1) * page_size
    query = select(models.Page, models.Site.name.label("site_name")).join(
        models.Site, models.Page.site_id == models.Site.id
    ).where(*conditions).order_by(desc(models.Page.scraped_at)).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for page_obj, site_name in rows:
        page_detail = schemas.PageDetail.from_orm(page_obj)
        page_detail.site_name = site_name
        
        # Manually fetch content using a separate query.
        content_result = await db.execute(
             select(models.PageContent)
            .where(models.PageContent.page_id == page_obj.id)
            .order_by(desc(models.PageContent.created_at))
            .limit(1)
        )
        content = content_result.scalar_one_or_none()
        if content:
             page_detail.latest_content = schemas.PageContentRead.from_orm(content)
        
        items.append(page_detail)
    
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        
    return schemas.PaginatedFeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
