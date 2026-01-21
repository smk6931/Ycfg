"""
트렌드 수집 비즈니스 로직
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Dict, Any
from loguru import logger
from datetime import datetime

from .models import Keyword, InstagramContent, YouTubeContent, NewsContent
from .schemas import TrendCollectionResponse
from ..clients.apify_client import ApifyService
from ..clients.youtube_client import YouTubeClient
from ..clients.rss_client import RSSClient
from ..clients.crawler_client import CrawlerClient

class TrendService:
    """트렌드 수집 및 분석 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.apify = ApifyService()
        self.youtube = YouTubeClient()
        self.news = RSSClient()
        self.crawler = CrawlerClient()

    async def collect_trending_contents(self, country: str) -> TrendCollectionResponse:
        """
        실시간 인기 콘텐츠 직접 수집 (키워드 중간 단계 없음)
        1. YouTube Trending (mostPopular)
        2. Google News Headlines (RSS)
        -> 바로 DB 저장
        """
        logger.info(f"🔥 실시간 인기 콘텐츠 수집 시작: {country}")
        
        # 더미 키워드 생성 (FK 요구사항 충족)
        today = datetime.now().strftime("%Y%m%d")
        dummy_keyword = f"Trending_{country}_{today}"
        
        # 더미 키워드 DB 저장
        keyword_obj = Keyword(
            keyword=dummy_keyword,
            country=country,
            trend_volume=0,
            rank=0
        )
        self.db.add(keyword_obj)
        await self.db.flush()  # ID 확보
        keyword_id = keyword_obj.id
        
        # 1. YouTube Trending 수집
        youtube_count = 0
        videos = await self.youtube.get_trending_videos(country, max_results=20)
        if videos:
            await self._save_youtube_contents(keyword_id, country, videos)
            youtube_count = len(videos)
            logger.info(f"✅ YouTube Trending: {youtube_count}개")
        
        # 2. Google News RSS 수집
        news_count = 0
        articles = await self.crawler._fetch_google_news_rss(country)
        if articles:
            # articles는 이미 Dict 형태 (keyword, country, rank 포함)
            # 우리는 title만 필요하므로 변환
            news_list = []
            for article in articles:
                news_list.append({
                    'title': article['keyword'],  # 뉴스 제목을 'keyword' 필드에서 가져옴
                    'source': 'Google News',
                    'description': '',
                    'url': '',  # RSS 수집 시 URL이 없을 수 있음
                    'published_at': datetime.now().isoformat()
                })
            
            await self._save_news_contents(keyword_id, country, news_list)
            news_count = len(news_list)
            logger.info(f"✅ Google News: {news_count}개")
        
        # 집계 업데이트
        await self._update_keyword_aggregates(keyword_id)
        await self.db.commit()
        
        total = youtube_count + news_count
        logger.info(f"🎉 실시간 콘텐츠 수집 완료: {total}개")
        
        return TrendCollectionResponse(
            success=True,
            message=f"실시간 인기 콘텐츠 {total}개 수집 완료",
            keywords_count=total
        )

    # ===== Private Helper Methods =====
    
    async def _save_youtube_contents(self, keyword_id: int, country: str, videos: List[Dict[str, Any]]):
        """유튜브 콘텐츠 저장"""
        for video in videos:
            stmt = select(YouTubeContent).where(YouTubeContent.video_id == video["video_id"])
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                content = YouTubeContent(
                    keyword_id=keyword_id,
                    keyword_country=country,
                    **video
                )
                self.db.add(content)
        
        await self.db.commit()
    
    async def _save_news_contents(self, keyword_id: int, country: str, articles: List[Dict[str, Any]]):
        """뉴스 콘텐츠 저장"""
        for article in articles:
            # URL이 없으면 중복 체크 생략하고 그냥 저장
            if article.get('url'):
                stmt = select(NewsContent).where(NewsContent.url == article["url"])
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    continue
            
            content = NewsContent(
                keyword_id=keyword_id,
                keyword_country=country,
                **article
            )
            self.db.add(content)
        
        await self.db.commit()
    
    async def _update_keyword_aggregates(self, keyword_id: int):
        """키워드별 집계 업데이트"""
        youtube_stmt = select(func.count()).select_from(YouTubeContent).where(YouTubeContent.keyword_id == keyword_id)
        news_stmt = select(func.count()).select_from(NewsContent).where(NewsContent.keyword_id == keyword_id)
        
        youtube_count = await self.db.scalar(youtube_stmt) or 0
        news_count = await self.db.scalar(news_stmt) or 0
        
        score = (youtube_count * 1.5) + (news_count * 1)
        
        update_stmt = (
            update(Keyword)
            .where(Keyword.id == keyword_id)
            .values(
                youtube_videos=youtube_count,
                news_count=news_count,
                score=score
            )
        )
        await self.db.execute(update_stmt)
        await self.db.commit()

    async def get_keyword_contents(self, keyword_id: int) -> Dict[str, Any]:
        """키워드 관련 콘텐츠 상세 조회"""
        keyword = await self.db.get(Keyword, keyword_id)
        if not keyword:
            return None

        stmt_news = select(NewsContent).where(NewsContent.keyword_id == keyword_id).limit(20)
        news_res = await self.db.execute(stmt_news)
        news_list = news_res.scalars().all()
        
        stmt_youtube = select(YouTubeContent).where(YouTubeContent.keyword_id == keyword_id).limit(10)
        yt_res = await self.db.execute(stmt_youtube)
        yt_list = yt_res.scalars().all()
        
        return {
            "keyword": keyword,
            "news": [{"title": n.title, "url": n.url, "source": n.source, "published_at": str(n.published_at)} for n in news_list],
            "youtube": [{"title": y.title, "url": y.url, "channel": y.channel, "views": y.views} for y in yt_list]
        }
