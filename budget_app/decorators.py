# 원래 CLI 함수 실행
# → 오류가 없으면 기존 결과 반환
# → 오류가 있으면 스택트레이스 대신 이해하기 쉬운 메시지 출력
# → 오류 종류에 따라 0이 아닌 종료 코드 반환



# 함수 자체를 타입으로 표현하기 위해 Callable을 가져옵니다.
from collections.abc import Callable

# 데코레이터를 적용한 뒤에도 원래 함수의 이름과 설명 같은 정보를
# 유지하기 위해 wraps를 가져옵니다.
from functools import wraps

# 위치 인자와 키워드 인자에 다양한 타입의 값이 들어올 수 있음을
# 표현하기 위해 Any를 가져옵니다.
from typing import Any


# CLI 실행 중 발생하는 공통 오류를 처리하는 데코레이터입니다.
def handle_cli_errors(
    # 정수형 종료 코드를 반환하는 함수를 전달받습니다.
    #
    # Callable[..., int]에서 ...은
    # 인자의 개수와 타입이 다양할 수 있다는 의미입니다.
    function: Callable[..., int],
) -> Callable[..., int]:
    # 데코레이터 적용 후에도 원래 함수의
    # 이름, 문서 문자열 등의 정보를 유지합니다.
    @wraps(function)

    # 원래 함수를 감싸서 실행할 내부 함수입니다.
    def wrapper(
        # 전달받은 위치 인자들을 모두 받습니다.
        *args: Any,

        # 전달받은 키워드 인자들을 모두 받습니다.
        **kwargs: Any,
    ) -> int:
        try:
            # 원래 함수를 같은 인자와 함께 실행합니다.
            # 정상 실행되면 원래 함수가 반환한 종료 코드를 그대로 반환합니다.
            return function(*args, **kwargs)

        # 사용자가 입력한 파일 경로에 파일이 없을 때 발생하는 오류입니다.
        except FileNotFoundError as exc:
            # 오류 원인을 출력합니다.
            print(
                f"[오류] 파일을 찾을 수 없습니다: {exc}"
            )

            # 사용자가 문제를 해결할 수 있도록 힌트를 출력합니다.
            print(
                "[힌트] 입력한 파일 경로를 확인하세요."
            )

            # 파일을 찾지 못한 오류 종료 코드로 2를 반환합니다.
            return 2

        # 파일이나 폴더에 접근 권한이 없을 때 발생하는 오류입니다.
        except PermissionError as exc:
            print(
                f"[오류] 파일 접근 권한이 없습니다: {exc}"
            )

            print(
                "[힌트] 파일이 다른 프로그램에서 "
                "열려 있는지 확인하세요."
            )

            # 권한 관련 오류 종료 코드로 3을 반환합니다.
            return 3

        # 날짜, 금액, 타입 등 입력값 검증에 실패했을 때 처리합니다.
        except ValueError as exc:
            # validators.py나 services.py에서 발생시킨
            # 구체적인 오류 메시지를 출력합니다.
            print(f"[오류] {exc}")

            print(
                "[힌트] 입력값과 명령어 옵션을 "
                "다시 확인하세요."
            )

            # 잘못된 입력값에 대한 오류 종료 코드로 4를 반환합니다.
            return 4

        # 사용자가 Ctrl+C를 눌러 프로그램을 중단했을 때 처리합니다.
        except KeyboardInterrupt:
            print(
                "\n[중단] 사용자가 프로그램을 종료했습니다."
            )

            # Ctrl+C 종료에 일반적으로 사용하는 130을 반환합니다.
            return 130

        # 파일 읽기, 쓰기, 경로 처리 등
        # 운영체제 수준의 파일 오류를 처리합니다.
        except OSError as exc:
            print(
                f"[오류] 파일 처리 중 문제가 발생했습니다: {exc}"
            )

            print(
                "[힌트] 저장 경로와 파일 상태를 "
                "확인하세요."
            )

            # 기타 파일 처리 오류 종료 코드로 5를 반환합니다.
            return 5

    # 데코레이터를 적용할 때 원래 함수 대신
    # 오류 처리 기능이 추가된 wrapper 함수를 반환합니다.
    return wrapper