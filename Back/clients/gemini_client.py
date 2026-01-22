"""
Google Gemini API 클라이언트
- 트렌드 키워드 추출 및 분석용
"""
import google.generativeai as genai
from typing import List, Dict, Any
from loguru import logger
import json
import re

from ..core.config import settings

class GeminiClient:
    def __init__(self):
        try:
            if not settings.GEMINI_API_KEY:
                logger.warning("⚠️ GEMINI_API_KEY가 설정되지 않았습니다.")
                self.model = None
                return

            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            logger.error(f"⚠️ Gemini Client 초기화 실패: {e}")
            self.model = None

    async def analyze_keywords(self, titles: List[str], country: str = "KR") -> List[Dict[str, Any]]:
        """
        제목 리스트를 받아 핵심 트렌드 키워드와 이유를 추출
        """
        if not self.model or not titles:
            return []

        # 프롬프트 구성
        prompt = f"""
        당신은 실시간 트렌드 분석 전문가입니다.
        아래 제공된 {len(titles)}개의 유튜브 및 뉴스 제목들을 분석하여,
        현재 가장 화제가 되고 있는 '핵심 트렌드 주제(Keyword)' 10개를 선정해주세요.

        [분석 대상 국가]: {country}

        [제목 목록]:
        {chr(10).join(titles[:100])} 
        (너무 많으면 상위 100개만 전송)

        [요구사항]:
        1. 단순한 단어가 아니라 '주제' 중심으로 키워드를 잡을 것 (예: '삼성' (X) -> '삼성전자 실적 발표' (O))
        2. 해외 이슈일 경우, 키워드 자체를 한국어로 번역한 필드('keyword_kr')를 반드시 포함할 것. (한국 이슈면 원본과 동일하게)
        3. 각 키워드가 선정된 이유(Insight)를 1문장으로 요약할 것 (한국어).
        4. 결과는 반드시 JSON 포맷으로 출력할 것.
        
        [출력 예시 JSON]:
        [
            {{
                "keyword": "Galaxy S24 Ultra Titanium",
                "keyword_kr": "갤럭시 S24 울트라 티타늄",
                "count": 15,
                "reason": "유튜버들의 언박싱 영상과 성능 비교 리뷰가 쏟아지며 화제"
            }},
            {{
                "keyword": "鬼滅の刃 無限城編",
                "keyword_kr": "귀멸의 칼날 무한성편",
                "count": 10,
                "reason": "극장판 새로운 시리즈 상영에 대한 높은 기대감"
            }}
        ]
        """

        try:
            # 비동기 실행을 위해 loop 활용이 이상적이나, 
            # google-generativeai의 async 지원 여부에 따라 동기 호출 후 executor 사용 고려.
            # 0.3.2 버전 이상에서는 async generate_content_async 지원함.
            
            logger.info(f"🤖 Gemini 분석 요청 (제목 {len(titles)}개)")
            response = await self.model.generate_content_async(prompt)
            
            text_response = response.text
            
            # JSON 파싱 (가끔 ```json ``` 같은 Markdown이 섞여올 수 있음)
            json_str = text_response.replace("```json", "").replace("```", "").strip()
            
            keywords = json.loads(json_str)
            
            logger.info(f"✅ Gemini 분석 완료: {len(keywords)}개 키워드")
            return keywords

        except Exception as e:
            logger.error(f"❌ Gemini 분석 실패: {e}")
            return []
