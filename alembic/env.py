import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

import os
import sys

# 프로젝트 루트 경로 추가 (Back 패키지 인식을 위해)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 프로젝트 설정 및 모델 임포트
from Back.core.config import settings
from Back.core.database import Base
# 모델들이 Base에 등록되도록 반드시 import 해야 함
from Back.trend import models

# Alembic Config 객체
config = context.config

# 로깅 설정 (alembic.ini 파일의 설정 사용)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 메타데이터 대상 설정 (Autogenerate를 위해 필수)
target_metadata = Base.metadata

# DB URL 설정을 환경 변수(settings)에서 가져오기
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """오프라인 마이그레이션 실행"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """동기 연결 컨텍스트에서 마이그레이션 실행"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """온라인 마이그레이션 실행 (비동기 처리)"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
