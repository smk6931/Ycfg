"""
트렌드 수집 API 엔드포인트
"""
from fastapi import APIRouter, Query
# from fastapi import Depends, ... (get_db 사용 안 함)

from .service import TrendService
# from .schemas import TrendCollectionResponse

router = APIRouter(prefix="/trend", tags=["Trend Collection"])


@router.post("/collect-trending")
async def collect_trending_contents(
    country: str = Query(..., description="국가 코드 (KR, US, JP 등)"),
    source: str = Query("auto", description="수집 소스 (auto, nate, reddit)")
):
    """실시간 인기 콘텐츠 수집 (YouTube + News + Nate/Reddit)"""
    service = TrendService()
    
    # 1. 수집 수행 (여기서 키워드 리스트 확보)
    collection_res = await service.collect_trending_contents(country, source)
    
    # 2. 수집된 콘텐츠 조회
    contents_res = await get_trending_contents(country=country, limit=50)
    
    # 3. 결과 병합 (UI 배너를 위해 top_keywords + ai_keywords 포함)
    return {
        **contents_res, # youtube, news 리스트
        "top_keywords": collection_res.top_keywords,
        "ai_keywords": collection_res.ai_keywords,
        "message": collection_res.message
    }


@router.get("/platform-keywords")
async def get_platform_keywords(
    country: str = Query(..., description="국가 코드 (KR, JP)")
):
    """플랫폼별 실시간 검색어 수집 (Nate, Yahoo Japan 등)"""
    service = TrendService()
    result = await service.get_platform_keywords(country)
    return result


@router.get("/trending/contents")
async def get_trending_contents(
    country: str = "KR",
    limit: int = 50
):
    """
    오늘 수집된 인기 콘텐츠 조회 (YouTube + News)
    """
    from .repositories.keyword_repo import KeywordRepository
    from .repositories.youtube_repo import YouTubeRepository
    from .repositories.news_repo import NewsRepository
    
    keyword_repo = KeywordRepository()
    youtube_repo = YouTubeRepository()
    news_repo = NewsRepository()

    # 1. 오늘자 키워드 ID 찾기
    keyword_obj = await keyword_repo.get_or_create_daily_keyword(country)
    
    if not keyword_obj:
        return {"youtube": [], "news": []}
    
    keyword_id = keyword_obj['id']
    
    # 2. 콘텐츠 조회 (Repo 사용 -> 결과는 Dict 리스트)
    yt_list = await youtube_repo.get_by_keyword(keyword_id, limit=limit)
    news_list = await news_repo.get_by_keyword(keyword_id, limit=limit)
    
    return {
        "youtube": [
            {
                "title": y['title'],
                "url": y['url'],
                "channel": y['channel'],
                "views": y['views'],
                "likes": y['likes'],
                "type": "video"
            } for y in yt_list
        ],
        "news": [
            {
                "title": n['title'],
                "url": n['url'],
                "source": n['source'],
                "published_at": str(n['published_at']),
                "type": "news"
            } for n in news_list
        ]
    }


@router.get("/trending/keywords")
async def get_trending_keywords(
    country: str = "KR",
    top_n: int = 20
):
    """
    오늘 수집된 콘텐츠에서 핵심 키워드 추출 (NLP 분석)
    """
    from .analyzer import KeywordAnalyzer
    
    # 먼저 콘텐츠 조회
    contents = await get_trending_contents(country=country, limit=100)
    
    # 키워드 분석
    analyzer = KeywordAnalyzer()
    keywords = await analyzer.extract_keywords(contents, country=country, top_n=top_n)
    
    return {
        "country": country,
        "keywords": keywords,
        "total_contents": len(contents.get('youtube', [])) + len(contents.get('news', []))
    }
