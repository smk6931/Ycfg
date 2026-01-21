# 🚀 키워드 수집 전략 및 기술 스택 (Keyword Collection Strategy)

본 문서는 프로젝트 'Trend Hunter AI'의 핵심인 **트렌드 키워드 수집 방법론**을 정의합니다.  
비용 효율성(Cost-Efficiency)과 데이터 안정성(Stability)을 고려하여 단계별 수집 전략을 채택합니다.

---

## 1. 1단계: 무료 기반 구축 (Initial Phase - Cost Efficiency)
초기에는 비용이 들지 않는 라이브러리와 공개 RSS를 최대한 활용하여 시스템을 구축합니다.

### (1) Google Trends RSS Feed (★ Primary)
가장 안정적이고 차단 위험이 적은 방식입니다.
- **방식**: `feedparser` 라이브러리로 XML 데이터 파싱
- **URL**: `https://trends.google.com/trends/trendingsearches/daily/rss?geo={국가코드}`
- **지원 국가**: 한국(KR), 미국(US), 일본(JP), 대만(TW) 등
- **장점**: API 키 불필요, 완전 무료.
- **단점**: 제공하는 데이터 필드가 제한적 (키워드, 트래픽 근사치, 뉴스 링크 정도).

### (2) pytrends (Python Library)
구글 트렌드 비공식 API로, 파이썬에서 가장 널리 쓰이는 라이브러리입니다.
- **방식**: 구글 트렌드 백엔드를 직접 호출
- **코드 예시**:
  ```python
  from pytrends.request import TrendReq
  pytrends = TrendReq(hl='ko', tz=540)
  df = pytrends.trending_searches(pn='south_korea')
  ```
- **장점**: 코드가 간결하고 실시간(Realtime) 트렌드 접근 가능(미국 등).
- **단점**: 과도한 요청 시 Google의 **429 Too Many Requests** 차단 발생 가능 (Proxy 필요).

### (3) Signal.bz (한국 특화)
네이버/다음 실검 폐지 후 한국 이슈를 파악하기 좋은 사이트입니다.
- **방식**: `requests` + `BeautifulSoup` 크롤링
- **용도**: 한국 내 급상승 이슈 보완용.

---

## 2. 2단계: 유료 및 안정화 (Stabilization Phase - Reliability)
서비스 규모가 커지거나 무료 방식이 차단될 경우 도입하는 유료 솔루션입니다.

### (1) SerpApi (Google Trends API)
- **특징**: 전 세계 1위 검색 엔진 데이터 공급자. Proxy 관리나 파싱 로직 불필요.
- **가격**: 월 $50~ (무료 체험 가능).
- **추천 시점**: `pytrends`나 `RSS`가 빈번하게 차단될 때 "돈으로 해결"하는 가장 확실한 방법.

### (2) Apify (Web Scraper Cloud)
- **특징**: 단순 트렌드뿐만 아니라 **Instagram, YouTube** 등 SNS 심층 데이터를 긁어올 때 필수.
- **활용**: 현재 프로젝트의 '심층 분석(Deep Analysis)' 모드에서 사용 중.

---

## 3. 3단계: AI 분석 및 가치 창출 (AI Value Addition)
단순히 "무엇이 떴나"를 넘어 **"왜 떴나"**를 분석합니다.

### (1) OpenAI (GPT-4o) & Perplexity
- **역할**: 수집된 키워드에 대한 '이유 분석' 및 '콘텐츠 생성'.
- **프롬프트 예시**:
  > "현재 '두바이 초콜릿'이 트렌딩하는 이유를 뉴스 기사 3개를 요약해서 설명해주고, 블로그 포스팅용 제목 5개를 뽑아줘."
- **구현**: 현재 `Back/clients/openai_client.py`에 구현됨.

---

## ✅ 개발자 추천 테크트리 (Roadmap)

1.  **Start (Current)**:
    *   **Daily Trends**: Google Trends RSS (무료)
    *   **Deep Dive**: Apify (선택적 유료)
    *   **Analysis**: OpenAI GPT-4o
2.  **Scale-up**:
    *   RSS 차단 빈도 증가 시 → **Proxy 도입** 또는 **SerpApi 전환**
    *   한국 이슈 부족 시 → **Signal.bz 크롤러 추가**
