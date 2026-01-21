import feedparser
from typing import List, Dict, Any
from loguru import logger

class RSSClient:
    """RSS 피드 수집 (Google News & Trends)"""
    
    @staticmethod
    def _get_lang(country: str) -> str:
        return {"KR":"ko", "JP":"ja", "US":"en", "TW":"zh-TW", "ID":"id"}.get(country, "en")
    
    async def collect_news(self, keyword: str, country: str) -> List[Dict[str, Any]]:
        """Google News RSS 검색"""
        try:
            hl = self._get_lang(country)
            url = f"https://news.google.com/rss/search?q={keyword}&hl={hl}&gl={country}&ceid={country}:{hl}"
            
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries[:10]:
                # DB VARCHAR 길이 초과 방지 (Safe Truncate)
                title = entry.get("title", "")[:200]
                source = entry.get("source", {}).get("title", "Google News")[:100]
                description = entry.get("summary", "")[:500]
                url = entry.get("link", "")[:500]
                
                articles.append({
                    "title": title,
                    "source": source,
                    "description": description,
                    "published_at": entry.get("published", ""),
                    "url": url
                })
            
            logger.info(f"✅ News 수집 완료: {keyword} ({len(articles)}개)")
            return articles
            
        except Exception as e:
            logger.error(f"❌ News 수집 실패 ({keyword}): {e}")
            return []

    async def collect_google_trends_rss(self, country: str) -> List[Dict[str, Any]]:
        """
        Google Trends RSS (무료) 수집
        Apify 대안으로 사용
        """
        try:
            import requests # Lazy import
            
            # 국가 코드 매핑
            geo_map = {"KR": "KR", "US": "US", "JP": "JP", "TW": "TW", "ID": "ID"}
            geo = geo_map.get(country, "KR")

            # URL 최적화: 
            # 1. 도메인은 .com으로 통일 (리다이렉트 문제 방지)
            # 2. hl(언어) 파라미터 필수 추가
            hl = self._get_lang(country)
            
            # 일부 국가는 geo 코드가 다를 수 있음 (예: South Korea 등) 
            # 하지만 보통 KR, US, JP, TW, ID는 표준 코드 동작함.
            
            url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={country}&hl={hl}"
            
            # 중요: Google은 User-Agent 없으면 차단함
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # 1. requests로 데이터 가져오기
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ Google RSS 접근 실패 ({country}): {response.status_code}")
                return []
                
            # 2. 파싱
            feed = feedparser.parse(response.content)
            
            keywords = []
            if not feed.entries:
                logger.warning(f"⚠️ RSS 데이터 없음 (파싱 실패?): {country}, URL={url}")
                # 디버깅용: logger.debug(response.text[:200])
                
            for idx, entry in enumerate(feed.entries[:20]): # Top 20
                # 트래픽 정보 파싱 (예: "10000+")
                approx_traffic = entry.get("ht_approx_traffic", "0").replace("+", "").replace(",", "")
                try:
                    volume = int(approx_traffic)
                except:
                    volume = 0
                    
                keywords.append({
                    "keyword": entry.title,
                    "country": country,
                    "trend_volume": volume,
                    "rank": idx + 1
                })
            
            logger.info(f"✅ Google Trends (RSS) 수집 완료: {country} ({len(keywords)}개)")
            return keywords
            
        except Exception as e:
            logger.error(f"❌ Google Trends RSS 수집 실패 ({country}): {e}")
            return []
