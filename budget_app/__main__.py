# 이 모듈은 `python -m budget_app` 명령으로 프로그램을 실행할 때 사용되는 시작점입니다.



# budget_app/cli.py 파일에 있는 main 함수를 가져옵니다.
from budget_app.cli import main


# 이 파일이 직접 실행되었을 때만 아래 코드를 실행합니다.
if __name__ == "__main__":
    # main() 함수를 실행하고,
    # main()이 반환한 값을 프로그램의 종료 코드로 사용합니다.
    # 보통 0은 정상 종료, 0이 아닌 값은 오류 종료를 의미
    raise SystemExit(main())