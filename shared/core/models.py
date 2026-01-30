import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime, Text, Enum as PgEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class CrawlStrategy(str, Enum):
    SITEMAP = "sitemap"
    RSS = "rss"
    LINKS = "links"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class PageStatus(str, Enum):
    NEW = "new"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"

class DiscoverySource(str, Enum):
    SITEMAP = "sitemap"
    RSS = "rss"
    LINKS = "links"
    MANUAL = "manual"

class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    base_url: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sitemap_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rss_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # strategy default priority: sitemap -> rss -> links
    crawl_strategy: Mapped[CrawlStrategy] = mapped_column(PgEnum(CrawlStrategy), default=CrawlStrategy.SITEMAP)
    
    rate_limit_ms: Mapped[int] = mapped_column(Integer, default=1000)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    pages: Mapped[list["Page"]] = relationship("Page", back_populates="site")
    scrape_runs: Mapped[list["ScrapeRun"]] = relationship("ScrapeRun", back_populates="site")

class Page(Base):
    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    
    url: Mapped[str] = mapped_column(String, nullable=False)
    canonical_url: Mapped[str] = mapped_column(String, nullable=False)
    url_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    
    discovered_via: Mapped[DiscoverySource] = mapped_column(PgEnum(DiscoverySource), nullable=False)
    
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[PageStatus] = mapped_column(PgEnum(PageStatus), default=PageStatus.NEW, index=True)
    http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # REAL publication date
    
    content_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    site: Mapped["Site"] = relationship("Site", back_populates="pages")
    contents: Mapped[list["PageContent"]] = relationship("PageContent", back_populates="page")

class PageContent(Base):
    __tablename__ = "page_contents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pages.id"), nullable=False)
    
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default={})
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    page: Mapped["Page"] = relationship("Page", back_populates="contents")

class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_new: Mapped[int] = mapped_column(Integer, default=0)
    pages_processed: Mapped[int] = mapped_column(Integer, default=0)
    pages_failed: Mapped[int] = mapped_column(Integer, default=0)
    pages_skipped: Mapped[int] = mapped_column(Integer, default=0)
    
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    site: Mapped["Site"] = relationship("Site", back_populates="scrape_runs")

class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
