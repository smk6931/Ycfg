from googleapiclient.discovery import build
import asyncio
from typing import List, Dict, Any
from loguru import logger
from ..core.config import settings

class YouTubeClient:
    """YouTube Data API v3 클라이언트"""
    
    def __init__(self):
        try:
            self.youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
        except Exception as e:
            logger.error(f"⚠️ YouTube API 초기화 실패: {e}")
            self.youtube = None
    
    async def search_videos(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """비디오 검색 (비동기 래퍼)"""
        if not self.youtube:
            logger.warning(f"YouTube Client 미작동 (Skip: {keyword})")
            return []
            
        try:
            loop = asyncio.get_event_loop()
            
            def _execute():
                return self.youtube.search().list(
                    q=keyword,
                    part="snippet",
                    type="video",
                    maxResults=max_results
                ).execute()
                
            response = await loop.run_in_executor(None, _execute)
            
            videos = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")
                
                videos.append({
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "url": f"https://youtube.com/watch?v={video_id}"
                })
            
            logger.info(f"✅ YouTube 수집 완료: {keyword} ({len(videos)}개)")
            return videos
            
        except Exception as e:
            logger.error(f"YouTube 검색 실패: {str(e)}")
            return []
    
    async def get_trending_videos(self, country: str = "KR", max_results: int = 20) -> List[Dict[str, Any]]:
        """
        YouTube 실시간 인기 영상 수집 (Trending)
        """
        if not self.youtube:
            logger.warning("YouTube API 키가 없어 인기 영상을 수집할 수 없습니다.")
            return []
        
        try:
            loop = asyncio.get_event_loop()
            
            def _fetch():
                request = self.youtube.videos().list(
                    part="snippet,statistics",
                    chart="mostPopular",
                    regionCode=country,
                    maxResults=max_results
                )
                return request.execute()
            
            response = await loop.run_in_executor(None, _fetch)
            
            videos = []
            for item in response.get('items', []):
                snippet = item['snippet']
                stats = item.get('statistics', {})
                
                videos.append({
                    'video_id': item['id'],
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'url': f"https://youtube.com/watch?v={item['id']}",
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'published_at': snippet['publishedAt']
                })
            
            logger.info(f"✅ YouTube Trending 수집 성공 ({country}): {len(videos)}개")
            return videos
            
        except Exception as e:
            logger.error(f"YouTube Trending 수집 실패: {str(e)}")
            return []
