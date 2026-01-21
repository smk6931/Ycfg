================================================================================
Hybrid 데이터베이스 설계 (PostgreSQL + pgvector)
================================================================================

작성일: 2026-01-20
목적: 트렌드 데이터의 관계형 저장 및 AI 활용을 위한 벡터 임베딩 저장 설계


데이터베이스 정보
================================================================================
- DBMS: PostgreSQL 15+
- Extension: `vector` (pgvector 설치 필수)
  명령어: `CREATE EXTENSION IF NOT EXISTS vector;`


주요 테이블 스키마
================================================================================

1. trends_master (트렌드 원장)
--------------------------------------------------
발견된 트렌드 키워드를 통합 관리하는 메타 테이블.
벡터 컬럼(`embedding`)을 포함하여 의미 기반 검색 지원.

CREATE TABLE trends_master (
    id              BIGSERIAL PRIMARY KEY,
    keyword         VARCHAR(255) NOT NULL,
    country         VARCHAR(2) DEFAULT 'KR',
    
    -- AI 벡터 임베딩 (1536차원: OpenAI text-embedding-3-small 기준)
    embedding       vector(1536),
    
    first_seen_at   TIMESTAMP DEFAULT NOW(),
    last_seen_at    TIMESTAMP DEFAULT NOW(),
    
    -- 통계 정보
    frequency_count INTEGER DEFAULT 1,     -- 발견 빈도
    source_diversity INTEGER DEFAULT 1,    -- 몇 개의 소스에서 떴는지
    
    UNIQUE(keyword, country)
);
-- 벡터 검색 인덱스 (HNSW)
CREATE INDEX ON trends_master USING hnsw (embedding vector_cosine_ops);


2. raw_collections (수집 원본)
--------------------------------------------------
무료/유료 API에서 긁어온 날것의 데이터를 저장.
어떤 API가 이 키워드를 물어왔는지 기록하여 성능 비교.

CREATE TABLE raw_collections (
    id              BIGSERIAL PRIMARY KEY,
    trend_id        BIGINT REFERENCES trends_master(id),
    
    source_name     VARCHAR(50) NOT NULL,  -- 'google_rss', 'apify_instagram', 'naver_datalab'
    source_type     VARCHAR(10) NOT NULL,  -- 'FREE', 'PAID'
    
    raw_title       TEXT,                  -- 수집된 제목
    raw_url         TEXT,                  -- 링크
    raw_data        JSONB,                 -- API 전체 응답 저장 (JSON)
    
    collected_at    TIMESTAMP DEFAULT NOW()
);


3. keyword_analytics (분석/통계)
--------------------------------------------------
기간별 키워드 점수 및 순위 스냅샷.

CREATE TABLE keyword_analytics (
    id              BIGSERIAL PRIMARY KEY,
    trend_id        BIGINT REFERENCES trends_master(id),
    
    date            DATE DEFAULT CURRENT_DATE,
    
    hot_score       DECIMAL(10,2),         -- 자체 산정 점수
    rank_change     INTEGER,               -- 순위 변동
    
    created_at      TIMESTAMP DEFAULT NOW()
);


데이터 처리 흐름
================================================================================

1. Upsert & Embedding
--------------------------------------------------
새로운 키워드 "갤럭시 S25"가 들어오면:
1) OpenAI API로 "갤럭시 S25" -> `[0.12, -0.5, ...]` 벡터 생성.
2) `trends_master`에 키워드 및 벡터 저장.
3) 만약 이미 있는 키워드라면 `last_seen_at` 업데이트.

2. 시맨틱 검색 (AI 활용 예시)
--------------------------------------------------
사용자: "IT 기기 관련 트렌드만 보여줘"
SQL:
SELECT keyword, 1 - (embedding <=> '[IT 기기 벡터값]') AS similarity
FROM trends_master
WHERE 1 - (embedding <=> '[IT 기기 벡터값]') > 0.7
ORDER BY similarity DESC;


비교 분석 쿼리 (무료 vs 유료)
================================================================================

-- 유료 API(Apify)에서만 발견된 키워드 찾기
SELECT m.keyword 
FROM trends_master m
JOIN raw_collections r ON m.id = r.trend_id
WHERE r.source_type = 'PAID'
  AND m.id NOT IN (
      SELECT trend_id FROM raw_collections WHERE source_type = 'FREE'
  );
