
import asyncio
from typing import List
from loguru import logger
from openai import AsyncOpenAI
from ..core.config import settings

class AIKeywordExtractor:
    """GenAI를 활용한 마케팅 키워드 추출"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def extract_marketing_keywords(self, contents: List[dict]) -> List[str]:
        """
        수집된 콘텐츠(YouTube, News)를 분석하여 마케팅 활용 가능한 키워드 추출
        
        :param contents: [{'title': '...', 'type': 'video/news'}, ...]
        :return: ['키워드1', '키워드2', ...]
        """
        if not contents:
            return []
        
        # 콘텐츠 제목만 추출
        titles = [item.get('title', '') for item in contents[:30]]  # 최대 30개
        combined_text = "\n".join(titles)
        
        try:
            logger.info("🤖 GenAI 마케팅 키워드 추출 시작...")
            
            prompt = f"""다음은 최근 인기 있는 콘텐츠들의 제목입니다.
                        이 콘텐츠들을 분석하여 마케팅 및 콘텐츠 제작에 활용할 수 있는 핵심 키워드를 추출해주세요.

                        요구사항:
                        1. 단어 또는 짧은 구문 형태로 추출 (2-5글자)
                        2. 마케팅 가치가 높은 키워드 우선
                        3. 중복 제거
                        4. 최대 15개
                        5. 각 키워드는 쉼표로 구분
                        6. 응답은 오직 키워드 리스트만 (설명 없이)

                        콘텐츠 제목:
                        {combined_text}

                        마케팅 키워드:"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 트렌드 분석 및 마케팅 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            
            # 쉼표로 분리하여 리스트로 변환
            keywords = [k.strip() for k in result.split(',') if k.strip()]
            
            logger.info(f"✅ GenAI 키워드 추출 완료: {len(keywords)}개 - {keywords[:5]}...")
            return keywords[:15]
            
        except Exception as e:
            logger.error(f"❌ GenAI 키워드 추출 실패: {e}")
            return []
