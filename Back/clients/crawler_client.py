"""
Google Trends API 차단을 우회하기 위한 크롤러 클라이언트
1. 한국(KR): Signal.bz (실시간 검색어) 직접 크롤링
2. 글로벌: Google News RSS 헤드라인 파싱 (절대 막히지 않음)
"""
import requests
from bs4 import BeautifulSoup
import feedparser
from typing import List, Dict, Any
from loguru import logger
import re
import asyncio

class CrawlerClient:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    async def collect_trends(self, country: str) -> List[Dict[str, Any]]:
        """국가별 최적의 방법으로 트렌드 수집"""
        loop = asyncio.get_event_loop()
        
        # 1. 한국: 실시간 검색어 사이트 크롤링 시도
        if country == 'KR':
            keywords = await loop.run_in_executor(None, self._crawl_signal_bz)
            if keywords:
                return keywords
                
        # 2. 글로벌/실패 시: Google News RSS 사용 (API 차단 없음)
        return await loop.run_in_executor(None, lambda: self._fetch_google_news_rss(country))

    def _crawl_signal_bz(self) -> List[Dict[str, Any]]:
        """Signal.bz 실시간 검색어 크롤링"""
        try:
            url = "https://www.signal.bz/"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code != 200:
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            # Signal.bz의 순위 텍스트 클래스
            ranks = soup.select(".rank-text")
            
            if not ranks:
                # 2024년 이후 UI 변경 대비: 다른 선택자 시도
                # 네이버 실검 대체 사이트는 구조가 자주 안 바뀜
                return []
                
            keywords = []
            for i, rank in enumerate(ranks[:20]):
                word = rank.text.strip()
                if word:
                    keywords.append({
                        "keyword": word,
                        "country": "KR",
                        "trend_volume": 0,
                        "rank": i + 1
                    })
            
            if keywords:
                logger.info(f"✅ Signal.bz 크롤링 성공 (KR): {len(keywords)}개")
                return keywords
                
        except Exception as e:
            logger.warning(f"⚠️ Signal.bz 크롤링 에러: {e}")
            
        return []

    def _fetch_google_news_rss(self, country: str) -> List[Dict[str, Any]]:
        """Google News RSS 헤드라인 파싱"""
        try:
            # 국가별 RSS URL 설정
            configs = {
                "KR": {"hl": "ko", "gl": "KR", "ceid": "KR:ko"},
                "US": {"hl": "en-US", "gl": "US", "ceid": "US:en"},
                "JP": {"hl": "ja", "gl": "JP", "ceid": "JP:ja"},
                "TW": {"hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"},
                "ID": {"hl": "id", "gl": "ID", "ceid": "ID:id"}
            }
            
            config = configs.get(country, configs["US"])
            url = f"https://news.google.com/rss?hl={config['hl']}&gl={config['gl']}&ceid={config['ceid']}"
            
            feed = feedparser.parse(url)
            
            keywords = []
            for i, entry in enumerate(feed.entries[:20]):
                # 제목에서 매체명 제거 (예: "제목 - 조선일보" -> "제목")
                title = entry.title
                if ' - ' in title:
                    title = title.rsplit(' - ', 1)[0]
                
                keywords.append({
                    "keyword": title, # 뉴스 제목 자체가 이슈 키워드
                    "country": country,
                    "trend_volume": 0,
                    "rank": i + 1
                })
                
            if keywords:
                logger.info(f"✅ Google News RSS 수집 성공 ({country}): {len(keywords)}개")
                return keywords
                
        except Exception as e:
            logger.error(f"❌ Google News RSS 에러 ({country}): {e}")
            
        return []
