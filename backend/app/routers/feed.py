from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from shared.core import models, schemas, database

router = APIRouter(prefix="/feed", tags=["feed"])

@router.get("/new", response_model=List[schemas.PageDetail])
async def get_new_feed(
    since: datetime,
    site_id: UUID = Query(None),
    limit: int = 100,
    db: AsyncSession = Depends(database.get_db)
):
    """
    Devuelve páginas processed donde (scraped_at > since) o (first_seen_at > since).
    Incluye extracted_text completo.
    """
    query = select(models.Page, models.Site.name.label("site_name")).join(
        models.Site, models.Page.site_id == models.Site.id
    )
    
    if site_id:
        query = query.where(models.Page.site_id == site_id)
        
    query = query.where(
        models.Page.status == models.PageStatus.PROCESSED
    ).where(
        or_(
            models.Page.scraped_at > since,
            models.Page.first_seen_at > since
        )
    ).order_by(desc(models.Page.scraped_at)).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Needs optimization to avoid N+1 queries, but keeping it simple for now. 
    # In production, use joinedload for contents.
    
    response = []
    for page_obj, site_name in rows:
        page_detail = schemas.PageDetail.from_orm(page_obj)
        page_detail.site_name = site_name
        
        # Manually fetch content using a separate query or join.
        # Let's do a simple query for now.
        content_result = await db.execute(
             select(models.PageContent)
            .where(models.PageContent.page_id == page_obj.id)
            .order_by(desc(models.PageContent.created_at))
            .limit(1)
        )
        content = content_result.scalar_one_or_none()
        if content:
             page_detail.latest_content = schemas.PageContentRead.from_orm(content)
        
        response.append(page_detail)
        
    return response
