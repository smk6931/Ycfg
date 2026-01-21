"""
트렌드 수집 데이터 모델
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Keyword(Base):
    """트렌드 키워드 테이블"""
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200), nullable=False, index=True)
    country = Column(String(10), nullable=False, index=True)
    trend_volume = Column(Integer, default=0)
    rank = Column(Integer, default=0)
    
    # 수집 메타데이터
    keyword_collected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 집계 필드 (외래 데이터 카운트)
    instagram_posts = Column(Integer, default=0)
    youtube_videos = Column(Integer, default=0)
    news_count = Column(Integer, default=0)
    score = Column(Float, default=0.0)  # 종합 점수
    
    # 관계 설정 (1:N)
    instagram_contents = relationship("InstagramContent", back_populates="keyword_ref", cascade="all, delete-orphan")
    youtube_contents = relationship("YouTubeContent", back_populates="keyword_ref", cascade="all, delete-orphan")
    news_contents = relationship("NewsContent", back_populates="keyword_ref", cascade="all, delete-orphan")
    
    # 복합 인덱스 (국가별 키워드 검색 최적화)
    __table_args__ = (
        Index('ix_keywords_country_collected', 'country', 'keyword_collected_at'),
    )


class InstagramContent(Base):
    """인스타그램 콘텐츠 테이블"""
    __tablename__ = "instagram_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    
    # 인스타그램 고유 정보
    post_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(100))
    caption = Column(Text)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    timestamp = Column(String(50))  # ISO 형식 문자열
    url = Column(String(300))
    
    # 수집 메타
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    keyword_country = Column(String(10))
    
    # 관계
    keyword_ref = relationship("Keyword", back_populates="instagram_contents")


class YouTubeContent(Base):
    """유튜브 콘텐츠 테이블"""
    __tablename__ = "youtube_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    
    # 유튜브 고유 정보
    video_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(300))
    channel = Column(String(200))
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    published_at = Column(String(50))
    url = Column(String(300))
    
    # 수집 메타
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    keyword_country = Column(String(10))
    
    # 관계
    keyword_ref = relationship("Keyword", back_populates="youtube_contents")


class NewsContent(Base):
    """뉴스 콘텐츠 테이블"""
    __tablename__ = "news_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    
    # 뉴스 고유 정보
    title = Column(String(300))
    source = Column(String(100))
    description = Column(Text)
    published_at = Column(String(50))
    url = Column(String(500), unique=True)
    
    # 수집 메타
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    keyword_country = Column(String(10))
    
    # 관계
    keyword_ref = relationship("Keyword", back_populates="news_contents")
