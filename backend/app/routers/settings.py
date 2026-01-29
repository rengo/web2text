from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.core import database, models
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingBase(BaseModel):
    key: str
    value: str

class SettingUpdate(BaseModel):
    value: str

class SettingResponse(SettingBase):
    class Config:
        from_attributes = True

@router.get("/", response_model=List[SettingResponse])
async def get_settings(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Setting))
    return result.scalars().all()

@router.get("/{key}", response_model=SettingResponse)
async def get_setting(key: str, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Setting).where(models.Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.put("/{key}", response_model=SettingResponse)
async def update_setting(key: str, setting_update: SettingUpdate, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Setting).where(models.Setting.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        setting = models.Setting(key=key, value=setting_update.value)
        db.add(setting)
    else:
        setting.value = setting_update.value
    
    await db.commit()
    await db.refresh(setting)

    # If it's a worker-related setting, notify the worker
    if key in ["scrape_interval_minutes", "lookback_days"]:
        from sqlalchemy import text
        import json
        payload = json.dumps({"command": "reload_settings"})
        await db.execute(text(f"NOTIFY worker_commands, '{payload}'"))
        await db.commit()

    return setting
