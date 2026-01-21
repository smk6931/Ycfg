from openai import AsyncOpenAI
import json
from typing import List, Dict, Any, Optional
from loguru import logger
from ..core.config import settings

class OpenAIClient:
    """OpenAI GPT 클라이언트 (트렌드 추천 및 분석)"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("⚠️ OpenAI API 키가 설정되지 않았습니다.")
    
    async def recommend_keywords(self, category: str, country: str = "KR") -> List[str]:
        """주제별 트렌드 키워드 추천"""
        if not self.client:
            return [category]

        try:
            logger.info(f"🤖 AI 키워드 추천 요청: {category} ({country})")
            
            prompt = f"""
            Task: Recommend 5 currently trending keywords or specific topics related to the category '{category}' in {country}.
            
            Rules:
            1. Keywords must be specific emerging trends, product names, slang, or viral news topics. Avoid broad terms.
            2. Example: If category is 'Food', recommend specific hits like 'Dubai Chocolate' or 'Yogurt Ice Cream'.
            3. Return ONLY a JSON array of strings: ["keyword1", "keyword2", ...]. No markdown.
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": "You are a trend expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            keywords = json.loads(content)
            return keywords[:5] if isinstance(keywords, list) else [category]
            
        except Exception as e:
            logger.error(f"❌ AI 키워드 추천 실패: {e}")
            return [category]

    async def analyze_trend_reason(self, keyword: str, articles: List[Dict[str, Any]]) -> str:
        """뉴스 데이터를 바탕으로 트렌드 원인 3줄 요약"""
        if not self.client or not articles:
            return "분석 불가 (데이터 부족 또는 API 미설정)"

        try:
            context = "\n".join([f"- {a.get('title')}: {a.get('description')}" for a in articles[:3]])
            
            prompt = f"""
            Analyze why '{keyword}' is trending based on the news below.
            Summarize the reason in 3 bullet points in Korean.
            
            News:
            {context}
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a trend analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ AI 분석 실패: {e}")
            return "트렌드 원인 분석 실패"
