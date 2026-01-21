"""
Google Trends 수집 (PyTrends 라이브러리 사용)
RSS 404 문제를 우회하기 위해 Realtime Trending Searches를 우선 사용
"""
from pytrends.request import TrendReq
from typing import List, Dict, Any
from loguru import logger
import asyncio
import pandas as pd

class PytrendsClient:
    """PyTrends 기반 무료 트렌드 수집기"""
    
    def __init__(self):
        # urllib3 호환성 이슈 방지를 위해 기본 설정 사용
        self.pytrends = TrendReq(hl='ko', tz=540)
    
    async def collect_google_trends(self, country: str) -> List[Dict[str, Any]]:
        """
        Google Trends 수집 (Realtime -> Daily 순서로 시도)
        """
        loop = asyncio.get_event_loop()
        keywords = []
        
        # 1. Realtime Trends 시도 (최신 데이터, 국가코드 사용)
        try:
            def _fetch_realtime():
                # Realtime은 국가코드(KR, US 등)를 그대로 사용
                return self.pytrends.realtime_trending_searches(pn=country)
            
            df = await loop.run_in_executor(None, _fetch_realtime)
            
            if df is not None and not df.empty:
                logger.info(f"✅ Realtime Trends 수집 성공: {country}")
                # Realtime 결과는 보통 'title', 'entity_names' 등의 컬럼을 가짐
                # title이 키워드임
                target_col = 'title' if 'title' in df.columns else df.columns[0]
                
                for idx, row in df.iterrows():
                    keyword_text = str(row[target_col])
                    if keyword_text:
                        keywords.append({
                            "keyword": keyword_text,
                            "country": country,
                            "trend_volume": 0, # Realtime은 볼륨 미제공
                            "rank": idx + 1
                        })
                return keywords
                
        except Exception as e:
            logger.warning(f"⚠️ Realtime 수집 실패 ({country}): {e} -> Daily 모드로 전환")
            
        # 2. Daily Trends 시도 (전통적인 방식, RSS 기반)
        try:
            # Daily는 영문 풀네임(south_korea) 사용
            country_map = {
                "KR": "south_korea",
                "US": "united_states", 
                "JP": "japan",
                "TW": "taiwan",
                "ID": "indonesia"
            }
            pn = country_map.get(country, "south_korea")
            
            def _fetch_daily():
                return self.pytrends.trending_searches(pn=pn)
            
            df = await loop.run_in_executor(None, _fetch_daily)
            
            if df is not None and not df.empty:
                 logger.info(f"✅ Daily Trends 수집 성공: {country}")
                 # Daily 결과는 0번 컬럼이 키워드
                 for idx, row in df.iterrows():
                    keyword_text = str(row[0])
                    if keyword_text:
                        keywords.append({
                            "keyword": keyword_text,
                            "country": country,
                            "trend_volume": 0,
                            "rank": idx + 1
                        })
                 return keywords
                 
        except Exception as e:
            # 404 에러 등
            logger.error(f"❌ Daily Trends 수집 실패 ({country}): {e}")
        
        return []
