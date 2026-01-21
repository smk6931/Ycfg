from apify_client import ApifyClient
from typing import List, Dict, Any
from loguru import logger
from ..core.config import settings

class ApifyService:
    """Apify 기반 서비스 (Google Trends, Instagram)"""
    
    def __init__(self):
        self.client = ApifyClient(settings.APIFY_TOKEN)
    
    async def collect_google_trends(self, country: str, timeframe: str = "24") -> List[Dict[str, Any]]:
        """Google Trends 수집"""
        try:
            run_input = {
                "enableTrendingSearches": True,
                "trendingSearchesCountry": country,
                "trendingSearchesTimeframe": timeframe
            }
            
            run = self.client.actor("data_xplorer/google-trends-fast-scraper").call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            keywords = []
            for item in dataset_items:
                if "trending_searches" in item and item["trending_searches"]:
                    for idx, trend in enumerate(item["trending_searches"][:20]):
                        keywords.append({
                            "keyword": trend.get("term") or trend.get("query", ""),
                            "country": country,
                            "trend_volume": self._parse_volume(trend.get("trend_volume_formatted", "0")),
                            "rank": idx + 1
                        })
            
            logger.info(f"✅ Trends 수집 완료: {country} ({len(keywords)}개)")
            return keywords
        except Exception as e:
            logger.error(f"❌ Trends 수집 실패 ({country}): {e}")
            return []
            
    async def collect_instagram_posts(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Instagram 해시태그 수집"""
        try:
            run_input = {
                "hashtags": [keyword],
                "resultsType": "posts",
                "resultsLimit": limit
            }
            # 실제 실행 시 토큰 소모 주의
            # run = self.client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
            # items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            # (임시) 개발 중 토큰 절약을 위해 빈 리스트 반환하거나 실제 호출 주석 처리
            # 필요 시 주석 해제하여 사용
            # 지금은 에러 방지를 위해 실제 호출 코드를 살려두되, 예외 발생 시 로그 출력
            
            run = self.client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
            items = self.client.dataset(run["defaultDatasetId"]).list_items().items

            posts = []
            for item in items:
                posts.append({
                    "post_id": item.get("id") or item.get("shortCode", ""),
                    "username": item.get("ownerUsername", ""),
                    "caption": (item.get("caption") or "")[:500],
                    "likes": item.get("likesCount", 0),
                    "comments": item.get("commentsCount", 0),
                    "timestamp": item.get("timestamp", ""),
                    "url": item.get("url") or f"https://instagram.com/p/{item.get('shortCode', '')}"
                })
            
            logger.info(f"✅ Insta 수집 완료: {keyword} ({len(posts)}개)")
            return posts
            
        except Exception as e:
            # Apify Actor 관련 에러는 자주 발생하므로 Warning 처리
            logger.warning(f"⚠️ Insta 수집 실패 ({keyword}): {e}")
            return []

    @staticmethod
    def _parse_volume(volume_str: str) -> int:
        """10K+ -> 10000 변환"""
        if not volume_str: return 0
        s = volume_str.upper().replace("+","").replace(",","")
        m = 1
        if "M" in s:
            m = 1000000; s = s.replace("M","")
        elif "K" in s:
            m = 1000; s = s.replace("K","")
        try:
            return int(float(s) * m)
        except:
            return 0
