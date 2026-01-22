"""
트렌드 키워드 분석 모듈
AI(Gemini)를 활용하여 수집된 콘텐츠에서 핵심 트렌드 주제를 도출
"""
from typing import List, Dict, Any
from loguru import logger
from ..clients.gemini_client import GeminiClient

class KeywordAnalyzer:
    """핵심 키워드 추출 및 분석 (AI Powered)"""
    
    def __init__(self):
        self.ai_client = GeminiClient()
    
    async def extract_keywords(self, contents: Dict[str, List[Dict]], country: str = "KR", top_n: int = 10) -> List[Dict[str, Any]]:
        """
        수집된 콘텐츠에서 AI를 통해 핵심 트렌드 키워드 추출
        """
        # 1. 제목 데이터 집계
        titles = []
        for video in contents.get('youtube', []):
            titles.append(video.get('title', ''))
        
        for news in contents.get('news', []):
            titles.append(news.get('title', ''))
            
        if not titles:
            return []
            
        # 2. AI 분석 요청
        try:
            keywords = await self.ai_client.analyze_keywords(titles, country)
            
            # top_n 개수 맞추기
            return keywords[:top_n]
            
        except Exception as e:
            logger.error(f"KeywordAnalyzer 에러: {e}")
            return []
