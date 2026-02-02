from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

from urllib.parse import quote_plus

# Default values
DEFAULT_USER = "postgres"
DEFAULT_PASS = "postgres"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = "5432"
DEFAULT_DB = "web2text"

# Check if DATABASE_URL is explicitly set (e.g. in some raw deployment)
# If not, construct it from components, ensuring password is encoded.
if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    user = os.getenv("POSTGRES_USER", DEFAULT_USER)
    password = os.getenv("POSTGRES_PASSWORD", DEFAULT_PASS)
    host = os.getenv("POSTGRES_HOST", DEFAULT_HOST)
    port = os.getenv("POSTGRES_PORT", DEFAULT_PORT)
    db_name = os.getenv("POSTGRES_DB", DEFAULT_DB)
    
    password_encoded = quote_plus(password)
    DATABASE_URL = f"postgresql+asyncpg://{user}:{password_encoded}@{host}:{port}/{db_name}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
