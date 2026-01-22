
import feedparser
from typing import List, Dict, Any
from loguru import logger
from ..utils.execution_utils import handle_exception

class RSSClient:
    """RSS 피드 수집 클라이언트"""
    
    @handle_exception(error_msg="Google News RSS 수집 실패", default=[])
    def fetch_google_news(self, country: str) -> List[Dict[str, Any]]:
        """Google News RSS 헤드라인 파싱"""
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
                "rank": i + 1,
                "url": entry.link,
                "published_at": entry.get("published", "")
            })
            
        if keywords:
            logger.info(f"✅ Google News RSS 수집 성공 ({country}): {len(keywords)}개")
            return keywords
            
        return []
