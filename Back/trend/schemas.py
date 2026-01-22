"""
트렌드 도메인 Pydantic 스키마
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


# ===== Keyword 스키마 =====
class KeywordBase(BaseModel):
    """키워드 기본 스키마"""
    keyword: str = Field(..., max_length=200)
    country: str = Field(..., max_length=10)
    trend_volume: int = 0
    rank: int = 0


class KeywordCreate(KeywordBase):
    """키워드 생성 시 입력"""
    pass


class KeywordInDB(KeywordBase):
    """DB에서 조회된 키워드"""
    id: int
    keyword_collected_at: datetime
    instagram_posts: int = 0
    youtube_videos: int = 0
    news_count: int = 0
    score: float = 0.0
    
    class Config:
        from_attributes = True


# ===== Instagram 스키마 =====
class InstagramContentBase(BaseModel):
    """인스타그램 콘텐츠 기본"""
    post_id: str
    username: Optional[str] = None
    caption: Optional[str] = None
    likes: int = 0
    comments: int = 0
    timestamp: Optional[str] = None
    url: Optional[str] = None


class InstagramContentCreate(InstagramContentBase):
    """인스타그램 수집 데이터 생성"""
    keyword_country: str


class InstagramContentInDB(InstagramContentBase):
    """DB 조회 결과"""
    id: int
    keyword_id: int
    collected_at: datetime
    
    class Config:
        from_attributes = True


# ===== YouTube 스키마 =====
class YouTubeContentBase(BaseModel):
    """유튜브 콘텐츠 기본"""
    video_id: str
    title: Optional[str] = None
    channel: Optional[str] = None
    views: int = 0
    likes: int = 0
    published_at: Optional[str] = None
    url: Optional[str] = None


class YouTubeContentCreate(YouTubeContentBase):
    """유튜브 수집 데이터 생성"""
    keyword_country: str


class YouTubeContentInDB(YouTubeContentBase):
    """DB 조회 결과"""
    id: int
    keyword_id: int
    collected_at: datetime
    
    class Config:
        from_attributes = True


# ===== News 스키마 =====
class NewsContentBase(BaseModel):
    """뉴스 콘텐츠 기본"""
    title: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None
    published_at: Optional[str] = None
    url: Optional[str] = None


class NewsContentCreate(NewsContentBase):
    """뉴스 수집 데이터 생성"""
    keyword_country: str


class NewsContentInDB(NewsContentBase):
    """DB 조회 결과"""
    id: int
    keyword_id: int
    collected_at: datetime
    
    class Config:
        from_attributes = True


# ===== API 요청/응답 스키마 =====
class TrendCollectionRequest(BaseModel):
    """트렌드 수집 요청"""
    countries: List[str] = ["KR", "JP", "TW", "US", "ID"]
    top_n_per_country: int = Field(20, ge=1, le=50)
    preferred_source: str = "auto"  # auto, nate, reddit, pytrends, signal
    deep_analysis: bool = False


class ManualKeywordRequest(BaseModel):
    """수동 키워드 입력 요청"""
    keywords: List[str]
    country: str = "KR"
    deep_analysis: bool = False



class TrendCollectionResponse(BaseModel):
    """트렌드 수집 결과"""
    success: bool
    message: str
    keywords_count: int
    top_keywords: List[str] = []
    ai_keywords: List[str] = []  # GenAI 추출 마케팅 키워드
    instagram_count: int = 0
    youtube_count: int = 0
    news_count: int = 0

class TrendRecommendationRequest(BaseModel):
    """트렌드 추천 요청"""
    category: str
    country: str = "KR"

class PlatformKeywordsResponse(BaseModel):
    """플랫폼 검색어 응답"""
    success: bool
    platform: str  # "nate", "yahoo_japan", etc.
    keywords: List[str] = []
    message: str = ""

