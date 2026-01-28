"""Database engine and session factory.

Swap DATABASE_URL to a postgres+asyncpg:// connection string for production.
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./queued_llm/jobs.db",
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    """FastAPI dependency that yields an async DB session."""
    async with async_session() as session:
        yield session
