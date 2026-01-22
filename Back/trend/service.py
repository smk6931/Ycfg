"""
트렌드 수집 비즈니스 로직
"""
from loguru import logger
from datetime import datetime

from .schemas import TrendCollectionResponse, PlatformKeywordsResponse

# API Clients
from ..clients.youtube_client import YouTubeClient
from ..clients.rss_client import RSSClient
from ..clients.nate_client import NateClient
from ..clients.reddit_client import RedditClient
from ..clients.yahoo_japan_client import YahooJapanClient
from ..clients.ai_keyword_extractor import AIKeywordExtractor

# Repositories
from .repositories.keyword_repo import KeywordRepository
from .repositories.youtube_repo import YouTubeRepository
from .repositories.news_repo import NewsRepository

class TrendService:
    """트렌드 수집 및 분석 서비스"""
    
    def __init__(self):
        # Clients
        self.youtube_client = YouTubeClient()
        self.rss_client = RSSClient()
        self.nate_client = NateClient()
        self.reddit_client = RedditClient()
        self.yahoo_japan_client = YahooJapanClient()
        self.ai_extractor = AIKeywordExtractor()
        
        # Repositories
        self.keyword_repo = KeywordRepository()
        self.youtube_repo = YouTubeRepository()
        self.news_repo = NewsRepository()

    async def collect_trending_contents(self, country: str, source: str = "auto") -> TrendCollectionResponse:
        """
        실시간 인기 콘텐츠 수집 로직 (Keyword Driven)
        :param source: 'auto', 'nate', 'reddit'
        """
        logger.info(f"🔥 실시간 인기 콘텐츠 수집 시작 ({country}, source={source})")
        
        # 1. 키워드 ID 확보
        keyword_obj = await self.keyword_repo.get_or_create_daily_keyword(country)
        keyword_id = keyword_obj['id']
        trend_keywords = []

        # 2. 트렌드 키워드 수집
        if source == "nate":
            if country == 'KR':
                trend_keywords = await self.nate_client.get_realtime_trends()
            else:
                logger.warning("⚠️ Nate는 한국(KR)만 지원합니다.")
                
        elif source == "reddit":
            trend_keywords = await self.reddit_client.get_global_trends()

        else: # source == "auto" or others
            if country == 'KR':
                # KR -> Nate 우선
                trend_keywords = await self.nate_client.get_realtime_trends()
                if not trend_keywords:
                    logger.warning("⚠️ Nate 수집 실패 -> Reddit(Global) 대체 시도")
                    trend_keywords = await self.reddit_client.get_global_trends()
            else:
                # KR 외 -> Reddit (Global)
                # Pytrends/Signal 제거로 인해 글로벌 소스는 Reddit이 유일함
                trend_keywords = await self.reddit_client.get_global_trends()


        # 수집 대상 키워드 선정 (Top 20)
        target_keywords = trend_keywords[:20] if trend_keywords else []
        
        if not target_keywords:
             logger.warning(f"⚠️ 수집된 키워드가 없습니다. (Source: {source}, Country: {country})")
             # 키워드가 없어도 '인급동' 등으로 콘텐츠는 채울 수 있음.
        else:
             logger.info(f"🎯 최종 수집 대상 키워드: {target_keywords}")

        total_videos = []
        total_news = []
        
        # 3. 키워드 기반 콘텐츠 수집
        if target_keywords:
            for keyword in target_keywords:
                # 3-1. YouTube 검색
                found_videos = await self.youtube_client.search_videos(keyword, max_results=3)
                total_videos.extend(found_videos)
                
                # 3-2. News 검색 (생략. 전체 뉴스에서 매칭하거나, 향후 검색 기능 추가)
        
        # [보완] 콘텐츠 부족 시 YouTube 인급동(Trending) 추가
        if len(total_videos) < 10:
             trending_videos = await self.youtube_client.get_trending_videos(country, max_results=10)
             total_videos.extend(trending_videos)

        # 4. 일반 뉴스(RSS) 수집 - 키워드 무관
        headlines = await self.rss_client.fetch_google_news(country)
        for hl in headlines:
            total_news.append({
                'title': hl['keyword'], 
                'source': 'Google News',
                'description': '',
                'url': hl.get('url', ''),
                'published_at': hl.get('published_at') or datetime.now().isoformat()
            })
            
        # 5. DB 저장
        unique_videos = {v['video_id']: v for v in total_videos}.values()
        unique_news = {n['url']: n for n in total_news if n.get('url')}.values()
        
        youtube_res = await self.youtube_repo.save_videos(keyword_id, country, list(unique_videos))
        await self.news_repo.save_articles(keyword_id, country, list(unique_news))
        
        logger.info(f"✅ 저장 완료: YouTube {len(unique_videos)}개, News {len(unique_news)}개")

        # 6. 통계 업데이트
        await self.keyword_repo.update_statistics(keyword_id)
        
        total = len(unique_videos) + len(unique_news)
        
        # 7. GenAI 마케팅 키워드 추출
        all_contents = list(unique_videos) + list(unique_news)
        ai_keywords = await self.ai_extractor.extract_marketing_keywords(all_contents)
        
        return TrendCollectionResponse(
            success=True,
            message=f"콘텐츠 {total}개 수집 완료 (키워드: {', '.join(target_keywords[:5])}...)",
            keywords_count=total,
            top_keywords=target_keywords,
            ai_keywords=ai_keywords
        )

    async def get_platform_keywords(self, country: str) -> PlatformKeywordsResponse:
        """
        플랫폼별 실시간 검색어 수집
        :param country: 'KR', 'JP', etc.
        :return: PlatformKeywordsResponse
        """
        logger.info(f"🔍 플랫폼 검색어 수집 시작 ({country})")
        
        if country == 'KR':
            keywords = await self.nate_client.get_realtime_trends()
            platform = "Nate"
        elif country == 'JP':
            keywords = await self.yahoo_japan_client.get_realtime_trends()
            platform = "Yahoo! Japan"
        else:
            return PlatformKeywordsResponse(
                success=False,
                platform="None",
                keywords=[],
                message=f"국가 {country}는 플랫폼 검색어를 지원하지 않습니다."
            )
        
        if keywords:
            return PlatformKeywordsResponse(
                success=True,
                platform=platform,
                keywords=keywords,
                message=f"{platform} 검색어 {len(keywords)}개 수집 완료"
            )
        else:
            return PlatformKeywordsResponse(
                success=False,
                platform=platform,
                keywords=[],
                message=f"{platform} 검색어 수집 실패"
            )
