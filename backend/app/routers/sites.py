from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID
import json

from shared.core import models, schemas, database
from backend.app import auth

router = APIRouter(prefix="/sites", tags=["sites"], dependencies=[Depends(auth.get_current_user)])

@router.post("/", response_model=schemas.SiteRead)
async def create_site(site: schemas.SiteCreate, db: AsyncSession = Depends(database.get_db)):
    db_site = models.Site(**site.dict())
    db.add(db_site)
    await db.commit()
    await db.refresh(db_site)
    return db_site

@router.get("/", response_model=List[schemas.SiteRead])
async def read_sites(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    stmt = (
        select(
            models.Site, 
            func.count(models.Page.id).filter(models.Page.status == models.PageStatus.PROCESSED).label("pages_count"),
            func.count(models.Page.id).filter(models.Page.status == models.PageStatus.NEW).label("pending_count")
        )
        .outerjoin(models.Page, models.Site.id == models.Page.site_id)
        .where(models.Site.deleted == False)
        .group_by(models.Site.id)
        .offset(skip).limit(limit)
    )
    result = await db.execute(stmt)
    
    sites_with_counts = []
    for site, p_count, pending in result:
        setattr(site, "pages_count", p_count)
        setattr(site, "pending_count", pending)
        sites_with_counts.append(site)
        
    return sites_with_counts

@router.get("/{site_id}", response_model=schemas.SiteRead)
async def read_site(site_id: UUID, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Site).where(models.Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@router.patch("/{site_id}", response_model=schemas.SiteRead)
async def update_site(site_id: UUID, site_update: schemas.SiteUpdate, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Site).where(models.Site.id == site_id))
    db_site = result.scalar_one_or_none()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    update_data = site_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_site, key, value)
    
    await db.commit()
    await db.refresh(db_site)
    return db_site

@router.post("/{site_id}/run")
async def run_site_scrape(site_id: UUID, db: AsyncSession = Depends(database.get_db)):
    """
    Triggers an immediate scrape for the given site by sending a NOTIFY event
    to the 'worker_commands' channel.
    """
    # Verify site exists
    result = await db.execute(select(models.Site).where(models.Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Send NOTIFY event
    # SQLAlchemy literal text is needed for NOTIFY
    from sqlalchemy import text
    payload = json.dumps({"command": "scrape", "site_id": str(site_id)})
    await db.execute(text(f"NOTIFY worker_commands, '{payload}'"))
    await db.commit()

    return {"message": f"Scrape triggered for site {site.name}"}

@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(site_id: UUID, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Site).where(models.Site.id == site_id))
    db_site = result.scalar_one_or_none()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    db_site.deleted = True
    await db.commit()
    return None
