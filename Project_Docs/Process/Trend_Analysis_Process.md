# 실시간 인기 콘텐츠 수집 및 처리 프로세스 (Trend Analysis Process)

## 1. 개요
본 문서는 `Trend Hunter AI` 프로젝트의 핵심 기능인 "국가별 실시간 인기 콘텐츠 수집 및 시각화" 프로세스의 기술적 구현 상세와 데이터 흐름을 정의합니다.

## 2. 아키텍처 및 데이터 흐름
시스템은 **Front-end (React)** 와 **Back-end (FastAPI)**, **Database (PostgreSQL)** 로 구성되며, 외부 API(YouTube) 및 크롤링(Google News, Signal.bz)을 통해 데이터를 수집합니다.

### 2.1 데이터 파이프라인
```
[User Interaction] -> [React Client] -> [FastAPI Router] -> [TrendService]
                                                                 |
            [DB (PostgreSQL)] <--- (Save/Update) ----+---- (Collect) ----> [External Sources]
                   ^                                 |                           1. YouTube API (Video)
                   |                                 |                           2. Google News RPC (News)
                   +---- (Query Result) -------------+                           3. Signal.bz (Keyword)
```

## 3. 단계별 상세 프로세스

### 3.1 요청 단계 (Request)
- **Component**: `TrendCollector.jsx`
- **Action**: 사용자가 국가를 선택하고 "수집" 버튼 클릭.
- **API Call**: `POST /trend/collect-trending?country={CODE}` 요청 전송.
- **State**: `loading` 상태 활성화, 에러/데이터 초기화.

### 3.2 수집 단계 (Collection)
- **Module**: `Back/trend/service.py` -> `collect_trending_contents()`
- **Logic**:
    1. **기본 키워드 생성**: `Trending_{Country}_{YYYYMMDD}` 형식의 앵커 키워드 생성 (DB 참조용).
    2. **YouTube 수집**:
        - `YouTubeClient`를 통해 `mostPopular` 차트 영상 수집.
        - **[Plan B]**: 한국(KR) 등 특정 국가 데이터 부재 시, `Signal.bz` 실시간 검색어 1위 키워드로 영상을 검색(`search`)하여 대체.
    3. **Google News 수집**:
        - `RSSClient`를 통해 Google News RSS 파싱.
    4. **실시간 검색어 (KR only)**:
        - `ScraperClient`로 Signal.bz 크롤링 데이터를 뉴스 리스트 최상단에 `🔥` 이모지와 함께 추가.

### 3.3 저장 및 중복 처리 단계 (Storage & Deduplication)
- **Module**: `TrendService` -> `_save_..._contents()`
- **Issue**: 유튜브/뉴스 데이터는 고유 ID(video_id, url)에 Unique 제약이 걸려 있어, 단순 저장 시 일별 중복 데이터 누락 문제 발생.
- **Solution (Hijacking Update)**:
    - 데이터 존재 여부를 먼저 확인 (`SELECT`).
    - **IF** 이미 존재: 해당 레코드의 `keyword_id`를 **현재 키워드 ID** 로 업데이트하고, `collected_at`, `views` 등을 최신화. (어제 데이터가 오늘 데이터로 갱생됨).
    - **ELSE** 신규: `INSERT` 수행.

### 3.4 응답 및 조회 단계 (Response)
- **Module**: `Back/trend/router.py`
- **Issue**: 한 트랜잭션 내에서 업데이트된 데이터를 즉시 조회하지 못하는 격리 수준 문제 발생 가능.
- **Solution**:
    - `service.collect...` 완료 후 **`db.expire_all()`** 을 호출하여 세션 캐시 초기화 및 최신 데이터 로드 강제.
    - `get_trending_contents`를 호출하여 `{ youtube: [...], news: [...] }` 전체 리스트 반환.

### 3.5 렌더링 단계 (Rendering)
- **Component**: `TrendCollector.jsx`
- **Processing**:
    - API 응답(`res`)을 받아 `setContents(res)` 수행.
    - 데이터 가공: 각 아이템에 `type`('video', 'news', 'keyword')과 `score` 부여.
    - 단일 리스트로 병합(`allItems`) 후 점수순 정렬.
- **Filtering**:
    - 상단 탭([All], [YouTube], [Google News], [실시간 검색어])에 따라 `filteredItems` 도출 하여 테이블 뷰(`<table>`)로 렌더링.

## 4. 주요 트러블슈팅 이력 (2026-01-21)
1. **API 응답 불일치**: axios response 객체 전체 반환 문제 -> `response.data` 반환으로 수정.
2. **데이터 0건 노출**: DB 중복 저장 Skip으로 인한 조회 누락 -> 중복 시 `keyword_id` 업데이트 로직으로 변경.
3. **Session Stale**: 수집 직후 조회 시 데이터 안 보임 -> `db.expire_all()` 추가로 해결.
4. **URL 길이 제한**: 뉴스 URL 500자 초과 오류 -> DB 컬럼 타입을 `TEXT`로 변경.

## 5. 시스템 리팩토링 이력 (2026-01-22)

### 5.1 모듈 분리 (Client Layer)
- **Before**: 단일 `CrawlerClient` 클래스에 RSS 파싱과 웹 스크래핑 기능이 혼재.
- **After**: 기능별로 역할을 명확히 분리.
  - `YouTubeClient` (`youtube_client.py`): YouTube Data API v3 전용 (공식 API).
  - `RSSClient` (`rss_client.py`): `feedparser`를 활용한 Google News RSS 파싱.
  - `ScraperClient` (`scraper_client.py`): `BeautifulSoup` 기반 웹 크롤링 (Signal.bz 등).
- **Benefit**: 단일 책임 원칙(SRP) 준수로 유지보수성 및 확장성 대폭 개선.

### 5.2 데이터 수집 방식 요약
1. **YouTube**: 공식 API (`videos().list` + `chart="mostPopular"`), API Key 필요.
2. **Google News**: 공개 RSS 피드 (`feedparser`), API Key 불필요.
3. **한국 실시간 검색어**: 웹 크롤링 (`BeautifulSoup` + `Signal.bz`), 보조 수단.

## 6. 향후 기능 고도화 계획 (Roadmap)

### 6.1 핵심 키워드 자동 추출 (NLP)
- **목표**: 수집된 제목/내용에서 "진짜 트렌드 키워드" 추출.
- **방식**: 형태소 분석기(KoNLPy, spaCy 등)를 활용하여 명사 추출 + 빈도 분석.
- **산출물**: "갤럭시 S24", "아시안컵", "비트코인" 등 단어 단위 키워드와 언급 횟수.

### 6.2 트렌드 점수(Scoring) 알고리즘 개선
- **현재**: 단순 카운트 기반 (`유튜브 * 1.5 + 뉴스 * 1`).
- **개선 방향**:
  - 유튜브 조회수/좋아요 수 반영.
  - 뉴스 게재 시각(최신성) 가중치.
  - 급상승 속도 계산 (단위 시간당 증가율).
- **산출물**: "실시간 급상승 키워드 TOP 10" 같은 정밀한 랭킹.

### 6.3 데이터 정합성 강화
- **이슈**: 같은 내용, 다른 제목의 기사/영상 중복.
- **해결**: 제목 유사도 알고리즘 (TF-IDF, Cosine Similarity) 또는 AI Embedding을 통한 중복 탐지.
