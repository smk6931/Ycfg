================================================================================
API 수집 전략 상세 설계
================================================================================

작성일: 2026-01-20
목적: 각 데이터 소스별 API 활용 방법 및 수집 전략 정의


전체 수집 프로세스 흐름
================================================================================

1단계: 트렌드 키워드 발굴
   |
   v
2단계: 키워드별 다중 소스 데이터 수집
   |
   v
3단계: 데이터 정규화 및 저장
   |
   v
4단계: 점수 산정 및 랭킹
   |
   v
5단계: 최종 리포트 생성


1. Google Trends API (Apify)
================================================================================

API 정보
---
제공업체: Apify (data_xplorer/google-trends-fast-scraper)
비용: 월 $7.99 (별도 구독)
URL: https://apify.com/data_xplorer/google-trends-fast-scraper

수집 가능 데이터
---
- 국가별 실시간 트렌딩 키워드 (Top 20)
- 키워드별 검색 인기도 지수
- 시간대별 트렌드 변화
- 관련 검색어 및 주제

지원 국가
---
- KR: 한국
- JP: 일본
- TW: 대만
- US: 미국
- ID: 인도네시아

수집 전략
---
1. 매일 오전 9시, 오후 3시, 오후 9시 (하루 3회) 실행
2. 국가별로 순차 수집
3. 수집 데이터 구조:
   {
     "keyword": "키워드명",
     "country": "KR",
     "trend_score": 85,
     "timestamp": "2026-01-20T09:00:00",
     "related_queries": ["관련1", "관련2"],
     "rising": true
   }

4. 중복 제거: 키워드 + 국가 + 날짜 기준
5. 급상승 키워드 별도 플래그 처리

활용 방법
---
- Python requests 라이브러리로 Apify API 호출
- API Key 환경변수 저장: APIFY_API_KEY
- 일일 호출 제한 고려하여 배치 처리


2. YouTube Data API v3
================================================================================

API 정보
---
제공업체: Google
비용: 무료 (일일 할당량 10,000 units)
공식문서: https://developers.google.com/youtube/v3

수집 가능 데이터
---
- 국가별 인기 동영상 (videos.list?chart=mostPopular)
- 채널 정보, 조회수, 좋아요, 댓글 수
- 동영상 설명 및 태그
- 게시 시간

지원 국가
---
- regionCode 파라미터로 KR, JP, TW, US, ID 지정

수집 전략
---
1. 매일 1회 (오전 10시) 국가별 Top 50 동영상 수집
2. 키워드 검색:
   - search.list API 활용
   - 트렌드 키워드를 쿼리로 사용
   - 최신순 정렬 (publishedAfter 파라미터)

3. 수집 데이터 구조:
   {
     "video_id": "dQw4w9WgXcQ",
     "title": "동영상 제목",
     "channel": "채널명",
     "view_count": 1000000,
     "like_count": 50000,
     "published_at": "2026-01-19T12:00:00Z",
     "country": "KR",
     "tags": ["태그1", "태그2"]
   }

4. 할당량 관리:
   - videos.list: 1 unit
   - search.list: 100 units
   - 하루 최대 100회 검색 가능

활용 방법
---
- google-api-python-client 라이브러리 사용
- API Key 환경변수: YOUTUBE_API_KEY
- 요청 샘플:
  youtube.videos().list(
    part="snippet,statistics",
    chart="mostPopular",
    regionCode="KR",
    maxResults=50
  ).execute()


3. Instagram Hashtag Scraper (Apify)
================================================================================

API 정보
---
제공업체: Apify (apify/instagram-hashtag-scraper)
비용: $2.3/1,000건 (Apify 기본 플랜 $29에 12,000건 포함)
URL: https://apify.com/apify/instagram-hashtag-scraper

수집 가능 데이터
---
- 해시태그별 최신 게시물
- 게시물 좋아요 수, 댓글 수
- 게시 시간, 작성자
- 게시물 텍스트, 이미지 URL

수집 전략
---
1. 트렌드 키워드를 해시태그로 변환하여 검색
2. 국가 필터링:
   - 작성자 프로필 위치 정보 활용
   - 게시물 언어 감지 (langdetect 라이브러리)

3. 수집 우선순위:
   - 좋아요 + 댓글 수 합산 기준 상위 100개

4. 수집 데이터 구조:
   {
     "post_id": "instagram_post_123",
     "hashtags": ["#트렌드", "#인기"],
     "likes": 5000,
     "comments": 200,
     "posted_at": "2026-01-19T15:30:00",
     "author": "username",
     "caption": "게시물 내용",
     "engagement_rate": 5.2
   }

5. 크레딧 절약 전략:
   - 키워드당 최대 50개 게시물만 수집
   - 하루 최대 10개 키워드 검색

활용 방법
---
- Apify Python Client 사용
- 환경변수: APIFY_TOKEN
- 비동기 처리로 수집 시간 단축


4. Google News RSS
================================================================================

API 정보
---
제공업체: Google
비용: 무료
URL: https://news.google.com/rss

수집 가능 데이터
---
- 최신 뉴스 제목, 링크
- 게시 시간
- 뉴스 소스

지원 국가/언어
---
- hl 파라미터: ko-KR, ja-JP, zh-TW, en-US, id-ID
- gl 파라미터: KR, JP, TW, US, ID

수집 전략
---
1. 키워드별 RSS 피드 구독:
   https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR

2. 매 시간마다 업데이트 확인
3. 수집 데이터 구조:
   {
     "title": "뉴스 제목",
     "link": "https://...",
     "published": "2026-01-20T08:00:00",
     "source": "매체명",
     "country": "KR",
     "keyword": "검색어"
   }

4. 중복 제거: URL 기준

활용 방법
---
- feedparser 라이브러리 사용
- 요청 샘플:
  import feedparser
  feed = feedparser.parse(rss_url)


5. Threads API (Meta)
================================================================================

API 정보
---
공식 API: https://developers.facebook.com/docs/threads
제약사항: 자신의 계정만 조작 가능, 타인 게시물 수집 제한

대안: Apify Threads Scraper (사설 API)
---
비용: Apify 기본 플랜에 포함 (사용량 기준 과금)
수집 가능: 트렌딩 게시물, 해시태그 검색

수집 전략
---
1. 공식 API 활용 (게시 용도):
   - 자동 게시 기능 구현
   - 게시 예약 기능

2. 사설 API 활용 (수집 용도):
   - 트렌딩 게시물 Top 20 수집
   - 해시태그별 인기 게시물 수집

3. 수집 데이터 구조:
   {
     "post_id": "threads_123",
     "text": "게시글 내용",
     "likes": 300,
     "replies": 50,
     "reposts": 20,
     "posted_at": "2026-01-20T10:00:00",
     "author": "username"
   }

활용 방법
---
- 공식 API: requests + OAuth 인증
- 사설 API: Apify Client


수집 데이터 통합 전략
================================================================================

1. 데이터 정규화
---
모든 소스의 데이터를 통일된 형식으로 변환:
{
  "id": "unique_id",
  "source": "google_trends | youtube | instagram | news | threads",
  "country": "KR",
  "keyword": "관련 키워드",
  "title": "제목/내용",
  "url": "원본 URL",
  "metrics": {
    "views": 10000,
    "likes": 500,
    "comments": 50,
    "shares": 20
  },
  "published_at": "2026-01-20T10:00:00",
  "collected_at": "2026-01-20T11:00:00"
}

2. 중복 제거 로직
---
- URL 기준 중복 제거
- 제목 유사도 분석 (cosine similarity > 0.8)
- 같은 키워드 + 같은 날짜 + 다른 소스 = 다출처 점수 증가

3. 데이터베이스 저장
---
테이블 구조:
- raw_data: 원본 데이터 저장
- normalized_data: 정규화된 데이터
- trending_keywords: 트렌드 키워드 목록
- daily_reports: 일일 분석 리포트


API 호출 스케줄
================================================================================

09:00  Google Trends (5개국) + YouTube (5개국)
10:00  Instagram (상위 10개 키워드)
11:00  News RSS (키워드별)
12:00  데이터 정규화 및 점수 산정
15:00  Google Trends (2차 수집)
16:00  Instagram (2차 수집)
21:00  Google Trends (3차 수집) + 최종 리포트 생성


에러 핸들링 및 재시도 전략
================================================================================

1. API 호출 실패 시
---
- 3회 재시도 (exponential backoff)
- 실패 로그 저장
- Slack/이메일 알림

2. 할당량 초과 시
---
- 대기 후 다음 날 재시도
- 우선순위 낮은 작업 스킵

3. 데이터 품질 검증
---
- 필수 필드 누락 시 제외
- 이상치 탐지 (급격한 수치 변화)


다음 문서
================================================================================

- 03_점수_산정_알고리즘.md
- 04_데이터베이스_스키마.md
- 05_프로젝트_구조.md
