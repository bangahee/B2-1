from collections.abc import Callable
from functools import wraps
from typing import Any


def handle_cli_errors(func: Callable[..., int]) -> Callable[..., int]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as exc:
            print(f"[오류] 파일을 찾을 수 없습니다: {exc}")
            print("[힌트] 파일 경로를 확인하세요.")
            return 1
        except ValueError as exc:
            print(f"[오류] {exc}")
            print("[힌트] 입력값을 다시 확인하세요.")
            return 1
        except KeyboardInterrupt:
            print("\n[중단] 사용자가 프로그램을 종료했습니다.")
            return 1
        except Exception as exc:
            print(f"[오류] 예상하지 못한 문제가 발생했습니다: {exc}")
            print("[힌트] 입력값과 저장 파일 상태를 확인하세요.")
            return 1

    return wrapper