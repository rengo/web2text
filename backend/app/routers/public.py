from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import hashlib

from shared.core.database import get_db
from shared.core import models

router = APIRouter(prefix="/public", tags=["public"])

async def verify_api_key(x_api_key: str = Header(...), db: AsyncSession = Depends(get_db)):
    """
    Dependency to verify the API key.
    The key provided by the client is hashed and compared with the stored hash.
    """
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    query = select(models.ApiKey).where(
        models.ApiKey.key_hash == key_hash,
        models.ApiKey.is_active == True
    )
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key"
        )
    return api_key

class PublicPageResponse(BaseModel):
    url: str
    canonical_url: str
    title: Optional[str]
    author: Optional[str] = None
    summary: Optional[str] = None
    image_url: Optional[str] = None
    language: Optional[str] = None
    published_at: Optional[datetime]
    scraped_at: Optional[datetime]
    content: Optional[str] = None
    content_html: Optional[str] = None
    
    class Config:
        from_attributes = True

class PublicSiteResponse(BaseModel):
    id: UUID
    name: str
    base_url: str
    pages: List[PublicPageResponse]
    
    class Config:
        from_attributes = True

@router.get("/sites/{site_id}", response_model=PublicSiteResponse)
async def get_site_content(
    site_id: UUID, 
    limit: int = Query(100, le=100),
    api_key: models.ApiKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch content for a specific site.
    Returns site details and the last N processed pages.
    """
    # Get Site
    site_query = select(models.Site).where(models.Site.id == site_id)
    result = await db.execute(site_query)
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    # Get Pages (Processed only, latest first)
    pages_query = (
        select(models.Page)
        .where(
            models.Page.site_id == site_id,
            models.Page.status == models.PageStatus.PROCESSED,
            models.Page.scraped_at.isnot(None)
        )
        .order_by(desc(models.Page.scraped_at))
        .limit(limit)
    )
    
    pages_result = await db.execute(pages_query)
    pages = pages_result.scalars().all()
    
    public_pages = []
    for page in pages:
        # Fetch latest content
        content_query = (
            select(models.PageContent)
            .where(models.PageContent.page_id == page.id)
            .order_by(desc(models.PageContent.created_at))
            .limit(1)
        )
        content_res = await db.execute(content_query)
        content_obj = content_res.scalar_one_or_none()
        
        public_pages.append(PublicPageResponse(
            url=page.url,
            canonical_url=page.canonical_url,
            title=page.title,
            author=page.author,
            summary=page.summary,
            image_url=page.image_url,
            language=page.language,
            published_at=page.published_at,
            scraped_at=page.scraped_at,
            content=content_obj.extracted_text if content_obj else None,
            content_html=content_obj.raw_html if content_obj else None
        ))
    
    return PublicSiteResponse(
        id=site.id,
        name=site.name,
        base_url=site.base_url,
        pages=public_pages
    )
