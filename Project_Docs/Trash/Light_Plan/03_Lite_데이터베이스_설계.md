================================================================================
Lite 데이터베이스 설계 (SQLite)
================================================================================

작성일: 2026-01-20
목적: 로컬 파일형 DB인 SQLite를 위한 심플한 테이블 구조 설계


DB 파일 위치
================================================================================
경로: `c:\GitHub\Ycfg\data\trend_light.db`
특징: 이 파일 하나만 복사하면 데이터 백업/이동 완료.


테이블 구조 (스키마)
================================================================================

1. keywords (수집된 키워드/주제)
--------------------------------------------------
수집된 모든 트렌드 키워드의 마스터 테이블.

CREATE TABLE keywords (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword         TEXT NOT NULL,
    country         TEXT DEFAULT 'KR',
    source          TEXT NOT NULL,         -- google, naver, youtube 등
    first_seen_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    count           INTEGER DEFAULT 1,     -- 중복 발견 횟수 (인기도 척도)
    UNIQUE(keyword, country, source)       -- 중복 저장 방지
);


2. trends_data (상세 데이터)
--------------------------------------------------
키워드와 관련된 상세 정보 (뉴스 링크, 조회수 등).

CREATE TABLE trends_data (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id      INTEGER,               -- keywords.id 참조
    title           TEXT,                  -- 뉴스/영상 제목
    url             TEXT,                  -- 링크
    meta_info       TEXT,                  -- 기타 정보 (조회수 등 JSON으로 저장)
    collected_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(keyword_id) REFERENCES keywords(id)
);


3. sync_log (구글 시트 연동 로그)
--------------------------------------------------
언제 마지막으로 구글 시트에 업데이트했는지 기록.

CREATE TABLE sync_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    status          TEXT,                  -- SUCCESS, FAIL
    records_count   INTEGER,               -- 전송한 행 개수
    synced_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);


데이터 처리 로직 (Python 예시)
================================================================================

1. 중복 처리 (Upsert)
--------------------------------------------------
키워드가 이미 있으면 `last_seen_at`과 `count`만 업데이트하고,
없으면 새로 만든다.

SQL:
INSERT INTO keywords (keyword, country, source) VALUES (?, ?, ?)
ON CONFLICT(keyword, country, source) 
DO UPDATE SET 
    last_seen_at = CURRENT_TIMESTAMP,
    count = count + 1;

2. 조회 (Reporting)
--------------------------------------------------
오늘 뜬 키워드 중 가장 많이 발견된 순서로 조회.

SQL:
SELECT source, keyword, count, last_seen_at 
FROM keywords 
WHERE date(last_seen_at) = date('now') 
ORDER BY count DESC 
LIMIT 50;
-> 이 결과를 구글 시트로 쏘면 됨.


구글 스프레드시트 구조 (목표)
================================================================================

[Sheet 1: 종합_랭킹]
| 순위 | 키워드 | 국가 | 출처 | 발견횟수 | 최근발견시각 | 관련링크(대표) |
|------|--------|------|------|----------|--------------|----------------|
| 1    | 손흥민 | KR   | All  | 15       | 13:00        | news.com/...   |

[Sheet 2: 구글_트렌드]
... (구글 원본 데이터)

[Sheet 3: 유튜브_인기]
... (유튜브 원본 데이터)
