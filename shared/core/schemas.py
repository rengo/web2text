from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, HttpUrl, Field

from shared.core.models import CrawlStrategy, PageStatus, DiscoverySource


# --- Auth Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# --- Site Schemas ---

class SiteBase(BaseModel):
    name: str
    base_url: str
    enabled: bool = True
    sitemap_url: Optional[str] = None
    rss_url: Optional[str] = None
    crawl_strategy: CrawlStrategy = CrawlStrategy.SITEMAP
    rate_limit_ms: int = 1000
    user_agent: Optional[str] = None

class SiteCreate(SiteBase):
    pass

class SiteUpdate(BaseModel):
    enabled: Optional[bool] = None
    sitemap_url: Optional[str] = None
    rss_url: Optional[str] = None
    rate_limit_ms: Optional[int] = None
    user_agent: Optional[str] = None
    crawl_strategy: Optional[CrawlStrategy] = None

class SiteRead(SiteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    pages_count: int = 0
    pending_count: int = 0

    class Config:
        from_attributes = True

# --- Page Schemas ---

class PageBase(BaseModel):
    url: str
    canonical_url: str
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    status: PageStatus
    discovery_source: DiscoverySource = Field(alias="discovered_via")

class PageRead(BaseModel):
    id: UUID
    site_id: UUID
    url: str
    canonical_url: str
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    status: PageStatus
    discovered_via: DiscoverySource
    site_name: Optional[str] = None
    http_status: Optional[int] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True

class PageContentRead(BaseModel):
    id: UUID
    extracted_text: str
    metadata: dict[str, Any] = Field(alias="metadata_")
    created_at: datetime

    class Config:
        from_attributes = True

class PageDetail(PageRead):
    latest_content: Optional[PageContentRead] = None

class PaginatedFeedResponse(BaseModel):
    items: list[PageDetail]
    total: int
    page: int
    page_size: int
    total_pages: int
