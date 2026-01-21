================================================================================
Database Architecture Strategy
================================================================================

작성일: 2026-01-20
수정일: 2026-01-20 (Async + Raw SQL 반영)
목적: YcFg 프로젝트의 데이터베이스 운영 철학 및 기술 스택 정의


1. Architecture Philosophy (아키텍처 철학)
================================================================================

- "Performance via Simplicity" (단순함이 곧 성능이다)
  복잡한 레이어를 줄이고, 데이터베이스와 가장 가까운 곳에서 로직을 제어한다.

- ORM의 불필요한 추상화(Overhead) 제거
  편리함 뒤에 숨겨진 'N+1 문제', '보이지 않는 쿼리 실행' 등을 원천 차단하고,
  SQL 본연의 강력한 기능과 최적화를 그대로 사용한다.

- 위임할 것은 위임한다
  SQL 작성은 개발자가 주도하되, 까다로운 DB Connection Pool 관리나
  Transaction Management(트랜잭션 보장)는 검증된 엔진에 맡긴다.


2. Technical Stack (기술 스택)
================================================================================

A. Engine: SQLAlchemy Core (Async)
--------------------------------------------------
- 선정 이유: "SQLAlchemy의 안정성(Pool/Transcation)" + "asyncpg의 압도적 속도" 결합.
- 구성: `create_async_engine` + `asyncpg` 드라이버.
- 역할: 비동기 Connection Pool 관리, 트랜잭션 문맥(Context) 보장, 자동 롤백.

B. Query: Raw SQL (text)
--------------------------------------------------
- 선정 이유: ORM 변환 비용 Zero. 가장 빠르고 직관적임.
- 활용: ORM 객체가 아닌, `text("SELECT * FROM ...")` 형태로 직접 작성.
- 장점: 복잡한 조인, 윈도우 함수, CTE 등을 제약 없이 사용 가능.

C. Interface: Custom Wrapper
--------------------------------------------------
- 전략: 자주 쓰는 패턴을 Async 함수 하나로 압축하여 생산성 극대화.
- 주요 함수 (비동기):
  1) await db.execute(query, params) -> Insert/Update/Delete
  2) await db.fetch_one(query, params) -> 단일 행 조회
  3) await db.fetch_all(query, params) -> 다중 행 조회
- 기대 효과:
  개발자는 `async with session:` 블록을 매번 쓰는 번거로움 없이,
  함수 호출 한 번으로 안전하게 쿼리를 실행함.


3. Implementation Plan (구현 계획)
================================================================================

1단계: Docker 환경 구축
- 이미지: ankane/pgvector (PostgreSQL + Vector Extension)
- 컨테이너명: YcFg_DB

2단계: Connection Module 개발 (src/core/database.py)
- `AsyncSession` 및 `async_sessionmaker` 설정.
- Context Manager(`@asynccontextmanager`)를 통한 안전한 세션 관리.

3단계: Wrapper Functions 구현
- 트랜잭션 실패 시 자동 `rollback` 보장.
- 연결 누수 방지를 위한 `finally: close` 처리.
