"""
데이터베이스 연결 및 세션 관리
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import settings

# 비동기 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# ORM Base
Base = declarative_base()


async def get_db() -> AsyncSession:
    """FastAPI 의존성 주입용 DB 세션"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
