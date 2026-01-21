"""
트렌드 수집 API 엔드포인트
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from .service import TrendService
from .schemas import TrendCollectionResponse

router = APIRouter(prefix="/trend", tags=["Trend Collection"])


@router.post("/collect-trending")
async def collect_trending_contents(
    country: str = Query(..., description="국가 코드 (KR, US, JP 등)"),
    db: AsyncSession = Depends(get_db)
):
    """실시간 인기 콘텐츠 수집 (YouTube + News + Signal)"""
    service = TrendService(db)
    await service.collect_trending_contents(country)
    
    # 수집 후 바로 전체 목록 조회해서 반환 (중복이어도 DB에 있으면 표시)
    return await get_trending_contents(country=country, limit=50, db=db)


@router.get("/trending/contents")
async def get_trending_contents(
    country: str = "KR",
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    오늘 수집된 인기 콘텐츠 조회 (YouTube + News)
    """
    from .models import Keyword, YouTubeContent, NewsContent
    from sqlalchemy import select
    from datetime import datetime
    
    # 오늘 날짜의 Trending 키워드 찾기
    today = datetime.now().strftime("%Y%m%d")
    dummy_keyword = f"Trending_{country}_{today}"
    
    stmt = select(Keyword).where(Keyword.keyword == dummy_keyword).order_by(Keyword.id.desc())
    result = await db.execute(stmt)
    keyword = result.scalars().first()
    
    if not keyword:
        return {"youtube": [], "news": []}
    
    # YouTube 조회
    yt_stmt = select(YouTubeContent).where(YouTubeContent.keyword_id == keyword.id).limit(limit)
    yt_res = await db.execute(yt_stmt)
    yt_list = yt_res.scalars().all()
    
    # News 조회
    news_stmt = select(NewsContent).where(NewsContent.keyword_id == keyword.id).limit(limit)
    news_res = await db.execute(news_stmt)
    news_list = news_res.scalars().all()
    
    return {
        "youtube": [
            {
                "title": y.title,
                "url": y.url,
                "channel": y.channel,
                "views": y.views,
                "likes": y.likes,
                "type": "video"
            } for y in yt_list
        ],
        "news": [
            {
                "title": n.title,
                "url": n.url,
                "source": n.source,
                "published_at": str(n.published_at),
                "type": "news"
            } for n in news_list
        ]
    }
