"""
트렌드 수집 비즈니스 로직
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Dict, Any
from loguru import logger
from datetime import datetime
import asyncio

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
        
        # 더미 키워드 중복 체크
        stmt = select(Keyword).where(Keyword.keyword == dummy_keyword).order_by(Keyword.id.desc())
        result = await self.db.execute(stmt)
        keyword_obj = result.scalars().first()
        
        if not keyword_obj:
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
        
        # [Plan B] 한국인데 Trending이 0개면 -> 실시간 검색어로 영상 검색
        if not videos and country == 'KR':
            logger.warning("⚠️ YouTube Trending 0개 -> 실시간 검색어로 대체 수집 시도")
            try:
                loop = asyncio.get_event_loop()
                signal_keywords = await loop.run_in_executor(None, self.crawler._crawl_signal_bz)
                if signal_keywords:
                    top_keyword = signal_keywords[0]['keyword']
                    logger.info(f"🔎 대체 검색어: {top_keyword}")
                    videos = await self.youtube.search_videos(top_keyword, max_results=10)
            except Exception as e:
                logger.error(f"Plan B 실패: {e}")

        if videos:
            await self._save_youtube_contents(keyword_id, country, videos)
            youtube_count = len(videos)
            logger.info(f"✅ YouTube Trending: {youtube_count}개")
        
        # 2. Google News RSS 수집
        news_count = 0
        loop = asyncio.get_event_loop()
        articles = await loop.run_in_executor(None, self.crawler._fetch_google_news_rss, country)
        
        # 3. (한국 전용) Signal.bz 실시간 검색어 수집
        if country == 'KR':
            try:
                signal_keywords = await loop.run_in_executor(None, self.crawler._crawl_signal_bz)
                if signal_keywords:
                    logger.info(f"✅ Signal.bz 추가: {len(signal_keywords)}개")
                    # 실검을 뉴스 리스트 앞단에 추가
                    for item in signal_keywords:
                        articles.insert(0, {
                            'keyword': f"🔥 {item['keyword']}", # 강조 표시
                            'url': '', # 실검은 URL 없음 (Google 검색 링크를 만들어줄 수도 있음)
                            'published_at': datetime.now().isoformat()
                        })
            except Exception as e:
                logger.warning(f"Signal.bz 수집 실패: {e}")

        if articles:
            # articles는 이미 Dict 형태 (keyword, country, rank 포함)
            # 우리는 title만 필요하므로 변환
            news_list = []
            for article in articles:
                news_list.append({
                    'title': article['keyword'],  # 뉴스 제목
                    'source': 'Google News' if 'keyword' in article and '🔥' not in article['keyword'] else '실시간 검색어',
                    'description': '',
                    'url': article.get('url', ''),
                    # 실검의 경우 구글 검색 URL 생성
                    'url': article.get('url') or (f"https://www.google.com/search?q={article['keyword'].replace('🔥 ', '')}" if '🔥' in article['keyword'] else ''),
                    'published_at':  article.get('published_at') or datetime.now().isoformat()
                })
            
            await self._save_news_contents(keyword_id, country, news_list)
            news_count = len(news_list)
            logger.info(f"✅ News + Signal: {news_count}개")
        
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
        logger.info(f"🎬 YouTube 저장 시작: keyword_id={keyword_id}, 영상 수={len(videos)}")
        saved_count = 0
        skipped_count = 0
        
        for idx, video in enumerate(videos):
            try:
                video_id = video.get("video_id")
                title = video.get("title", "제목 없음")[:50]
                logger.info(f"  [{idx+1}/{len(videos)}] 처리 중: {title}...")
                
                # 중복 체크
                stmt = select(YouTubeContent).where(YouTubeContent.video_id == video_id)
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # 이미 존재하는 영상이면, 현재 키워드(최신) 소속으로 업데이트
                    logger.info(f"    ♻️ 중복 영상 -> 최신 키워드({keyword_id})로 소속 변경 (video_id={video_id})")
                    existing.keyword_id = keyword_id
                    existing.collected_at = func.now() # 수집 시각도 갱신
                    # 조회수 등 최신 정보로 업데이트
                    existing.views = video.get("views", existing.views)
                    existing.likes = video.get("likes", existing.likes)
                    
                    skipped_count += 1
                    saved_count += 1 # 화면에 보여주기 위해 카운트 포함
                    # commit은 루프 밖에서 한 번에 함 (SQLAlchemy 객체 변경 감지)
                    continue
                
                # 저장 (신규)
                content = YouTubeContent(
                    keyword_id=keyword_id,
                    keyword_country=country,
                    **video
                )
                self.db.add(content)
                saved_count += 1
                logger.info(f"    ✅ 저장 예정 (누적 {saved_count}개)")
                
            except Exception as e:
                logger.error(f"    ❌ 저장 실패: {e}")
                continue
        
        await self.db.commit()
        logger.info(f"🎬 YouTube 저장 완료: 신규 {saved_count}개, 중복 {skipped_count}개, 총 커밋됨")
    
    async def _save_news_contents(self, keyword_id: int, country: str, articles: List[Dict[str, Any]]):
        """뉴스 콘텐츠 저장"""
        for article in articles:
            url = article.get('url', '')
            if not url:
                continue

            # URL 중복 체크
            stmt = select(NewsContent).where(NewsContent.url == url)
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                # 중복 뉴스 -> 최신 키워드로 소속 업데이트
                existing.keyword_id = keyword_id
                existing.collected_at = func.now()
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
