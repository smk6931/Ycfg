# 프로젝트 개발 및 에이전트 행동 수칙 (Development & Agent Rules)

## 1. 커맨드 실행 규칙 (Strict Command Policy)
- **직접 실행 금지 (NEVER Auto-Run):** 에이전트는 터미널 명령어를 직접 실행(`run_command`)해서는 안 된다.
- **제안 방식:** 반드시 "사용자가 터미널에 복사/붙여넣기 할 수 있는 형태"로 명령어를 텍스트로 제공한다.
- **가상환경 명시:** Python 관련 명령어는 반드시 가상환경 경로(`.\venv\Scripts\python`, `.\venv\Scripts\pip`)를 명시한다.
  - ❌ `python main.py`
  - ✅ `.\venv\Scripts\python main.py`

## 2. 소통 및 보고 규칙 (Communication & Reporting)
- **문제 원인 분석:** 에러 발생 시, 단순히 고치는 시도만 하지 말고 "무엇이 문제였는지" 기술적으로 설명한다.
- **결과 미리보기:** 코드를 수정하기 전에 "어디를 왜 수정하는지" 설명하고, 수정 후에는 "어떤 결과가 예상되는지" 보고한다.
- **침묵 금지:** 툴(Tool) 사용 결과만 나열하지 말고, 각 단계의 의미를 자연어로 설명한다.

## 3. 기술적 원인 분석 (Lesson Learned: Alembic & Asyncio)
- **Alembic 실행 오류:** `alembic` 명령어는 가상환경 밖에서 인식되지 않으므로, `python -m alembic` 또는 가상환경 내 실행 파일(`.\venv\Scripts\alembic`)을 사용해야 한다.
- **Asyncio 에러:** 비동기 함수(`async def`) 내에서 동기 함수를 호출할 때는 `loop.run_in_executor`를 사용하여 블로킹을 방지해야 한다.
- **DB StringDataRightTruncation:** URL 등 긴 텍스트가 들어갈 컬럼은 `String` 대신 `Text` 타입을 사용하여 길이 제한을 없애야 한다.
