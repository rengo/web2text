# Web2Text: Incremental News Scraper

A dockerized fullstack application for incremental scraping of news sites using Python, FastAPI, Postgres, and React.

## Features

- **Incremental Scraping**: Uses sitemap, RSS, or link crawling to discover new pages.
- **De-duplication**: Canonicalizes URLs and tracks content hashes to avoid redundant processing.
- **Strict Data Model**: Stores metadata, raw HTML (optional), and clean extracted text.
- **Date Extraction**: Uses a priority-based strategy (Metadata > JSON-LD > Regex) to find the *real* publication date.
- **Worker**: Independent process using APScheduler for robust cron-like execution.
- **Playwright Ready**: Includes infrastructure for JS-heavy sites (configurable via env).

## Architecture

- **Backend**: FastAPI (Port 8000)
- **Worker**: Python + APScheduler
- **Database**: Postgres 15
- **Frontend**: React + Vite (Port 3000)

## Getting Started

### Prerequisites
- Docker & Docker Compose

### Running the App

1. **Build and Start**:
   ```bash
   make up
   ```
   Or:
   ```bash
   docker compose up --build
   ```

2. **Initialize Database** (First run only):
   ```bash
   make migrate
   ```
   *Note: This runs Alembic migrations.*

3. **Seed Data**:
   ```bash
   make seed
   ```
   This populates the DB with demo sites:
   - **LM Neuquén**: Strategy=SITEMAP
   - **Clarín**: Strategy=SITEMAP + RSS backup

4. **Access UI**:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Verification
1. Go to `http://localhost:3000`.
2. Click "Sites" to see the seeded sites.
3. Click "Run Now" on a site to trigger immediate scraping (logs will appear in worker container).
4. Go to "Feed" to see discovered articles as they appear.

## Configuration
Environment variables in `docker-compose.yml`:
- `SCRAPE_INTERVAL_SECONDS`: How often the worker checks sites (default 600s).
- `PAGES_PER_RUN`: Max pages to process per cycle per site.
