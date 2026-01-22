"""
실행 관련 유틸리티 (에러 및 예외 처리 공통화)
"""
import asyncio
import functools
from typing import Any, Callable, Optional, TypeVar
from loguru import logger

T = TypeVar("T")

async def safe_run(
    func: Callable[..., T],
    *args,
    error_msg: str = "작업 실행 중 오류 발생",
    default: Any = None,
    reraise: bool = False,
    **kwargs
) -> Optional[T]:
    """
    함수(동기/비동기)를 안전하게 실행하고, 예외 발생 시 로그를 남김.
    
    Args:
        func: 실행할 함수 (함수명만 넘김)
        *args: 함수에 전달할 위치 인자
        error_msg: 에러 발생 시 로그에 찍을 메시지
        default: 에러 발생 시 반환할 기본값 (기본: None)
        reraise: True면 로그만 찍고 에러를 다시 던짐 (상위에서 처리 필요할 때)
        **kwargs: 함수에 전달할 키워드 인자
        
    Returns:
        함수 실행 결과 또는 default 값
        
    Usage:
        result = await safe_run(my_func, arg1, arg2, error_msg="함수 실패!", default=[])
    """
    try:
        # 1. 비동기 함수인지 확인하고 실행
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        
        # 2. 동기 함수라면
        else:
            # 동기 함수인데 async 환경에서 오래 걸리는 작업일 수 있으니 executor 고려 가능하나,
            # 여기서는 단순 래핑 목적으로 바로 실행 (필요 시 loop.run_in_executor 사용 권장)
            return func(*args, **kwargs)
            
    except Exception as e:
        logger.error(f"❌ {error_msg}: {str(e)}")
        if reraise:
            raise e
        return default

async def _execute_protected(func, error_msg, default, args, kwargs):
    """실제 실행 및 예외 처리를 담당하는 내부 헬퍼 함수"""
    try:
        # 비동기 함수면 await, 아니면 그냥 실행
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"❌ {error_msg} ({func.__name__}): {str(e)}")
        return default

def handle_exception(error_msg: str = "오류 발생", default: Any = None):
    """
    [데코레이터] 함수 실행 중 에러가 나면 안전하게 처리
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 복잡한 로직은 위쪽 헬퍼 함수로 위임 -> 코드가 깔끔해짐
            return await _execute_protected(func, error_msg, default, args, kwargs)
        return wrapper
    return decorator
