
import requests
from bs4 import BeautifulSoup
from typing import List
from loguru import logger
from ..utils.execution_utils import handle_exception

class YahooJapanClient:
    """Yahoo! Japan 실시간 검색어 수집 클라이언트"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    @handle_exception(error_msg="Yahoo Japan 트렌드 수집 실패", default=[])
    async def get_realtime_trends(self) -> List[str]:
        """
        Yahoo! Japan 실시간 급상승 검색어 수집
        :return: ['キーワード1', 'キーワード2', ...]
        """
        url = "https://search.yahoo.co.jp/realtime/search"
        logger.info(f"Yahoo Japan 트렌드 수집 시도: {url}")
        
        response = requests.get(url, headers=self.headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Yahoo Japan 접속 실패: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        keywords = []
        
        # Yahoo Japan 실시간 검색어 영역
        # 클래스명은 실제 사이트 구조에 따라 조정 필요
        # 일반적으로 ranking 또는 trend 관련 클래스 사용
        items = soup.select(".trend-ranking-list li a") or soup.select(".ranking-list li a")
        
        if not items:
            # 대체 셀렉터 시도
            items = soup.select("a[href*='search']")[:20]
        
        for item in items[:20]:  # Top 20
            text = item.get_text(strip=True)
            
            # 숫자나 특수문자만 있는 경우 제외
            if text and len(text) >= 2 and not text.isdigit():
                if text not in keywords:
                    keywords.append(text)
                    
        if keywords:
            logger.info(f"✅ Yahoo Japan 트렌드 수집 성공: {len(keywords)}개 - {keywords[:5]}")
            return keywords
            
        logger.warning("Yahoo Japan 키워드 추출 실패 (Selector 불일치)")
        return []
