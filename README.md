# Web2Text: Incremental News Scraper

A dockerized fullstack application for incremental scraping of news sites using Python, FastAPI, Postgres, and React.

## Features

- **Incremental Scraping**: Uses sitemap, RSS, or link crawling to discover new pages.
- **De-duplication**: Canonicalizes URLs and tracks content hashes to avoid redundant processing.
- **Strict Data Model**: Stores metadata, raw HTML (optional), and clean extracted text.
- **Strict Article Filtering**: Validates pages using JSON-LD (`NewsArticle`, `Article`) to ensure only real content is scraped.
- **Date Extraction**: Uses a priority-based strategy (Metadata > JSON-LD > Regex) to find the *real* publication date.

- **Worker**: Independent process using APScheduler for robust cron-like execution.
- **Playwright Ready**: Includes infrastructure for JS-heavy sites (configurable via env).
- **Smart Filtering**: Automatically ignores non-article pages (categories, tags, archives, etc.) during discovery.

## Filtering Logic

Web2Text employs a strict content-based filtering strategy to ensure high-quality data:

1.  **Discovery**: Links are gathered from Sitemaps, RSS feeds, and on-page links.
2.  **HTML Validation**: Before processing any content, the system downloads the page HTML and parses its **JSON-LD** structured data.
3.  **Schema Check**: The page is processed **only if** it contains a schema of type:
    *   `NewsArticle`
    *   `Article`
    *   `BlogPosting`
    *   `Report`
4.  **Skipping**: Pages that do not match these types (e.g., Categories, Tags, Author profiles, Homepages) are marked as `SKIPPED` and their content is not saved.

## Architecture

- **Backend**: FastAPI (Port 9000)
- **Worker**: Python + APScheduler
- **Database**: Postgres 15
- **Frontend**: React + Vite (Port 3010)

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
   - Frontend: [http://localhost:3010](http://localhost:3010)
   - API Docs: [http://localhost:9000/docs](http://localhost:9000/docs)

## Verification
1. Go to `http://localhost:3010`.
2. Click "Sites" to see the seeded sites.
3. Click "Run Now" on a site to trigger immediate scraping (logs will appear in worker container).
4. Go to "Feed" to see discovered articles as they appear.

## Configuration
Environment variables in `docker-compose.yml`:
- `SCRAPE_INTERVAL_SECONDS`: How often the worker checks sites (default 600s).
- `PAGES_PER_RUN`: Max pages to process per cycle per site.

## Production Deployment

For production deployment (e.g., on a DigitalOcean Droplet):

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd web2text
   ```

2. **Prepare Environment**:
   ```bash
   cp .env.prod.example .env
   # Edit .env and set VITE_API_URL to your public IP/Domain
   # e.g., VITE_API_URL=http://your-droplet-ip:9000
   ```

3. **Deploy**:
   ```bash
   make prod-up
   ```

The production setup includes:
- **Frontend**: Optimized build served by Nginx on port 80.
- **Backend**: FastAPI on port 9000.
- **Automatic Migrations**: A migration service runs automatically to set up the database on the first run.
- **Persistence**: Database data is stored in `./postgres_data_prod`.
