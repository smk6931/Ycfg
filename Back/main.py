"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from .core.config import settings
from .trend.router import router as trend_router

# 로거 설정
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)

# FastAPI 앱 생성
app = FastAPI(
    title="Keyword Trend Collector API",
    description="글로벌 트렌드 키워드 수집 및 분석 시스템",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(trend_router)


@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "Keyword Trend Collector",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("🚀 Keyword Trend Collector API 시작")
    logger.info(f"📊 DEBUG 모드: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    logger.info("👋 서버 종료")
