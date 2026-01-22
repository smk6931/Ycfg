
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from loguru import logger
from ..utils.execution_utils import handle_exception

class ScraperClient:
    """웹 스크래핑 클라이언트"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    @handle_exception(error_msg="Signal.bz 크롤링 실패", default=[])
    def crawl_signal_bz(self) -> List[Dict[str, Any]]:
        """Signal.bz 실시간 검색어 크롤링 (KR 전용)"""
        url = "https://www.signal.bz/"
        response = requests.get(url, headers=self.headers, timeout=5)
        
        if response.status_code != 200:
            logger.warning(f"Signal.bz 응답 실패: Status Code {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # Signal.bz의 순위 텍스트 클래스
        ranks = soup.select(".rank-text")
        
        if not ranks:
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
            
        return []
