# 이 모듈은 사용자가 입력한 명령어와 옵션을 분석하고,
# 적절한 서비스 기능을 호출한 뒤 결과를 출력하는 CLI 역할을 담당합니다.

import argparse
from typing import Any

from budget_app.decorators import handle_cli_errors
from budget_app.formatters import print_transactions
from budget_app.repositories import (
    BudgetRepository,
    CategoryRepository,
    DataPaths,
    TransactionRepository,
)
from budget_app.services import (
    BudgetService,
    CategoryService,
    CsvService,
    SummaryService,
    TransactionService,
)


# argparse의 기본 도움말 문구를 한국어로 구성하기 위한 클래스입니다.
class KoreanArgumentParser(argparse.ArgumentParser):
    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # argparse가 기본으로 추가하는 영어 help 옵션을 비활성화합니다.
        kwargs.setdefault("add_help", False)

        super().__init__(*args, **kwargs)

        # 한국어 설명이 포함된 도움말 옵션을 직접 추가합니다.
        self.add_argument(
            "-h",
            "--help",
            action="help",
            help="도움말을 출력하고 프로그램을 종료합니다.",
        )

        # 도움말의 기본 구역 제목을 한국어로 변경합니다.
        self._positionals.title = "명령어"
        self._optionals.title = "옵션"


# 프로그램에서 사용할 명령어와 옵션을 정의합니다.
def build_parser() -> argparse.ArgumentParser:
    # 프로그램 전체 명령어를 관리하는 최상위 파서입니다.
    parser = KoreanArgumentParser(
        prog="budget_app",
        description="파일 기반 가계부 콘솔 프로그램",
        epilog=(
            "사용 예시:\n"
            "  python -m budget_app list --limit 5\n"
            "  python -m budget_app search --category food\n"
            "\n"
            "명령어별 자세한 도움말:\n"
            "  python -m budget_app <명령어> --help"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # 기본 데이터 저장 폴더를 변경할 수 있는 공통 옵션입니다.
    parser.add_argument(
        "--data-dir",
        default="data",
        metavar="경로",
        help="데이터 저장 폴더 경로 (기본값: data)",
    )

    # add, list, search 등의 하위 명령어를 등록합니다.
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="사용 가능한 명령어",
        parser_class=KoreanArgumentParser,
    )

    # ------------------------------------------------------------------
    # add
    # ------------------------------------------------------------------

    subparsers.add_parser(
        "add",
        help="새 거래를 대화형으로 추가합니다.",
        description=(
            "날짜, 거래 타입, 카테고리, 금액, 메모, 태그를\n"
            "순서대로 입력하여 새로운 거래를 저장합니다."
        ),
        epilog="사용 예시: python -m budget_app add",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------

    list_parser = subparsers.add_parser(
        "list",
        help="최신순 거래 목록을 출력합니다.",
        description=(
            "저장된 거래를 날짜와 거래 ID를 기준으로\n"
            "최신순으로 출력합니다."
        ),
        epilog="사용 예시: python -m budget_app list --limit 5",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        metavar="개수",
        help="출력할 최대 거래 수 (기본값: 10)",
    )

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------

    search_parser = subparsers.add_parser(
        "search",
        help="조건에 따라 거래를 검색합니다.",
        description=(
            "날짜, 카테고리, 거래 타입, 메모, 태그 조건을 사용하여\n"
            "거래를 검색하고 최신순으로 출력합니다."
        ),
        epilog=(
            "사용 예시:\n"
            "  python -m budget_app search --category food\n"
            "  python -m budget_app search --type expense\n"
            "  python -m budget_app search "
            "--from 2026-07-01 --to 2026-07-31"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    search_parser.add_argument(
        "--from",
        dest="date_from",
        metavar="YYYY-MM-DD",
        help="검색 시작 날짜",
    )

    search_parser.add_argument(
        "--to",
        dest="date_to",
        metavar="YYYY-MM-DD",
        help="검색 종료 날짜",
    )

    search_parser.add_argument(
        "--category",
        metavar="카테고리",
        help="검색할 카테고리 이름",
    )

    search_parser.add_argument(
        "--type",
        choices=["income", "expense"],
        metavar="타입",
        help="검색할 거래 타입: income 또는 expense",
    )

    search_parser.add_argument(
        "--q",
        metavar="검색어",
        help="메모에 포함된 검색어",
    )

    search_parser.add_argument(
        "--tag",
        metavar="태그",
        help="거래에 포함된 태그",
    )

    # ------------------------------------------------------------------
    # summary
    # ------------------------------------------------------------------

    summary_parser = subparsers.add_parser(
        "summary",
        help="월별 수입·지출 요약을 출력합니다.",
        description=(
            "특정 월의 총수입, 총지출, 잔액, 예산 사용률과\n"
            "카테고리별 지출 TOP N을 출력합니다."
        ),
        epilog=(
            "사용 예시: "
            "python -m budget_app summary --month 2026-07 --top 3"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    summary_parser.add_argument(
        "--month",
        required=True,
        metavar="YYYY-MM",
        help="조회할 월",
    )

    summary_parser.add_argument(
        "--top",
        type=int,
        default=3,
        metavar="개수",
        help="출력할 지출 카테고리 순위 개수 (기본값: 3)",
    )

    # ------------------------------------------------------------------
    # budget
    # ------------------------------------------------------------------

    budget_parser = subparsers.add_parser(
        "budget",
        help="월별 예산을 설정하거나 조회합니다.",
        description="월별 예산 정보를 저장하고 조회합니다.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    budget_subparsers = budget_parser.add_subparsers(
        dest="budget_command",
        required=True,
        title="예산 하위 명령어",
        metavar="명령어",
        parser_class=KoreanArgumentParser,
    )

    # budget set
    budget_set_parser = budget_subparsers.add_parser(
        "set",
        help="월별 예산을 저장합니다.",
        description=(
            "특정 월의 예산을 새로 저장합니다.\n"
            "같은 월의 예산이 이미 있다면 새 금액으로 수정합니다."
        ),
        epilog=(
            "사용 예시: "
            "python -m budget_app budget set "
            "--month 2026-07 --amount 500000"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    budget_set_parser.add_argument(
        "--month",
        required=True,
        metavar="YYYY-MM",
        help="예산을 설정할 월",
    )

    budget_set_parser.add_argument(
        "--amount",
        type=int,
        required=True,
        metavar="금액",
        help="설정할 월 예산 금액",
    )

    # budget get
    budget_get_parser = budget_subparsers.add_parser(
        "get",
        help="저장된 월별 예산을 조회합니다.",
        description="특정 월에 저장된 예산을 조회합니다.",
        epilog=(
            "사용 예시: "
            "python -m budget_app budget get --month 2026-07"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    budget_get_parser.add_argument(
        "--month",
        required=True,
        metavar="YYYY-MM",
        help="예산을 조회할 월",
    )

    # ------------------------------------------------------------------
    # category
    # ------------------------------------------------------------------

    category_parser = subparsers.add_parser(
        "category",
        help="카테고리를 추가, 조회 또는 삭제합니다.",
        description="거래에서 사용할 카테고리를 관리합니다.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    category_subparsers = category_parser.add_subparsers(
        dest="category_command",
        required=True,
        title="카테고리 하위 명령어",
        metavar="명령어",
        parser_class=KoreanArgumentParser,
    )

    # category add
    category_subparsers.add_parser(
        "add",
        help="카테고리를 대화형으로 추가합니다.",
        description=(
            "사용자에게 카테고리 이름을 입력받아 저장합니다.\n"
            "카테고리는 소문자로 정리되어 저장됩니다."
        ),
        epilog="사용 예시: python -m budget_app category add",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # category list
    category_subparsers.add_parser(
        "list",
        help="카테고리 목록을 출력합니다.",
        description="현재 등록된 모든 카테고리를 정렬하여 출력합니다.",
        epilog="사용 예시: python -m budget_app category list",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # category remove
    category_remove_parser = category_subparsers.add_parser(
        "remove",
        help="카테고리를 삭제합니다.",
        description=(
            "사용되지 않는 카테고리를 삭제합니다.\n"
            "거래에서 사용 중인 카테고리는 삭제할 수 없습니다."
        ),
        epilog=(
            "사용 예시: "
            "python -m budget_app category remove --name coffee"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    category_remove_parser.add_argument(
        "--name",
        required=True,
        metavar="카테고리",
        help="삭제할 카테고리 이름",
    )

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------

    update_parser = subparsers.add_parser(
        "update",
        help="ID를 기준으로 거래를 수정합니다.",
        description=(
            "거래 ID를 기준으로 지정한 필드만 수정합니다.\n"
            "수정할 옵션을 하나 이상 입력해야 합니다."
        ),
        epilog=(
            "사용 예시:\n"
            "  python -m budget_app update "
            "--id TX-000001 --amount 20000\n"
            "  python -m budget_app update "
            '--id TX-000001 --memo "dinner"'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    update_parser.add_argument(
        "--id",
        required=True,
        metavar="거래ID",
        help="수정할 거래 ID (예: TX-000001)",
    )

    update_parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="변경할 거래 날짜",
    )

    update_parser.add_argument(
        "--type",
        choices=["income", "expense"],
        metavar="타입",
        help="변경할 거래 타입: income 또는 expense",
    )

    update_parser.add_argument(
        "--category",
        metavar="카테고리",
        help="변경할 카테고리 이름",
    )

    update_parser.add_argument(
        "--amount",
        type=int,
        metavar="금액",
        help="변경할 거래 금액",
    )

    update_parser.add_argument(
        "--memo",
        metavar="메모",
        help='변경할 메모 (빈 값으로 지우려면 --memo "")',
    )

    update_parser.add_argument(
        "--tags",
        metavar="태그",
        help="변경할 태그 목록 (쉼표로 구분)",
    )

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    delete_parser = subparsers.add_parser(
        "delete",
        help="ID를 기준으로 거래를 삭제합니다.",
        description="지정한 거래 ID에 해당하는 거래를 삭제합니다.",
        epilog=(
            "사용 예시: "
            "python -m budget_app delete --id TX-000001"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    delete_parser.add_argument(
        "--id",
        required=True,
        metavar="거래ID",
        help="삭제할 거래 ID (예: TX-000001)",
    )

    # ------------------------------------------------------------------
    # import
    # ------------------------------------------------------------------

    import_parser = subparsers.add_parser(
        "import",
        help="CSV 거래 데이터를 가져옵니다.",
        description=(
            "CSV 파일의 각 행을 검증하여 거래로 저장합니다.\n"
            "잘못된 행은 건너뛰고 행 번호와 오류 원인을 출력합니다."
        ),
        epilog=(
            "사용 예시: "
            "python -m budget_app import --from tests/import_mixed.csv"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    import_parser.add_argument(
        "--from",
        dest="source",
        required=True,
        metavar="CSV경로",
        help="가져올 CSV 파일 경로",
    )

    # ------------------------------------------------------------------
    # export
    # ------------------------------------------------------------------

    export_parser = subparsers.add_parser(
        "export",
        help="거래 데이터를 CSV로 내보냅니다.",
        description=(
            "월 또는 날짜 범위에 해당하는 거래를\n"
            "CSV 파일로 저장합니다."
        ),
        epilog=(
            "사용 예시:\n"
            "  python -m budget_app export "
            "--out export.csv --month 2026-07\n"
            "  python -m budget_app export "
            "--out export.csv "
            "--from 2026-07-01 --to 2026-07-31"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    export_parser.add_argument(
        "--out",
        required=True,
        metavar="CSV경로",
        help="생성할 CSV 파일 경로",
    )

    export_parser.add_argument(
        "--month",
        metavar="YYYY-MM",
        help="내보낼 거래의 월",
    )

    export_parser.add_argument(
        "--from",
        dest="date_from",
        metavar="YYYY-MM-DD",
        help="내보낼 거래의 시작 날짜",
    )

    export_parser.add_argument(
        "--to",
        dest="date_to",
        metavar="YYYY-MM-DD",
        help="내보낼 거래의 종료 날짜",
    )

    return parser


# 데이터 저장소와 서비스 객체를 생성하고 연결합니다.
def create_services(
    data_dir: str,
) -> tuple[
    TransactionService,
    CategoryService,
    BudgetService,
    SummaryService,
    CsvService,
]:
    # 데이터 폴더와 세 개의 JSONL 파일 경로를 준비합니다.
    paths = DataPaths(data_dir)
    paths.ensure_files()

    # 실제 파일 읽기와 쓰기를 담당하는 저장소 객체를 생성합니다.
    transaction_repo = TransactionRepository(paths)
    category_repo = CategoryRepository(paths)
    budget_repo = BudgetRepository(paths)

    # 업무 로직을 담당하는 서비스 객체를 생성합니다.
    transaction_service = TransactionService(
        transaction_repo,
        category_repo,
    )

    category_service = CategoryService(
        category_repo,
        transaction_repo,
    )

    budget_service = BudgetService(budget_repo)

    summary_service = SummaryService(
        transaction_repo,
        budget_repo,
    )

    csv_service = CsvService(
        transaction_service,
        transaction_repo,
    )

    return (
        transaction_service,
        category_service,
        budget_service,
        summary_service,
        csv_service,
    )


# 대화형 입력으로 받은 금액 문자열을 정수로 변환합니다.
def read_positive_integer(prompt: str) -> int:
    raw_value = input(prompt).strip()

    try:
        return int(raw_value)

    except ValueError as exc:
        raise ValueError(
            "금액은 정수로 입력해야 합니다."
        ) from exc


# add 명령어의 대화형 입력과 출력을 처리합니다.
def run_add(
    transaction_service: TransactionService,
) -> int:
    date = input("날짜(YYYY-MM-DD): ").strip()

    transaction_type = input(
        "타입(income/expense): "
    ).strip()

    category = input("카테고리: ").strip()

    amount = read_positive_integer(
        "금액(양수): "
    )

    memo = input(
        "메모(선택): "
    ).strip()

    tags = input(
        "태그(쉼표로 구분, 없으면 엔터): "
    ).strip()

    transaction = transaction_service.add_transaction(
        date=date,
        transaction_type=transaction_type,
        category=category,
        amount=amount,
        memo=memo,
        tags_text=tags,
    )

    print(f"[저장 완료] id={transaction.id}")
    return 0


# summary 명령어에서 계산 결과를 보기 좋게 출력합니다.
def run_summary(
    summary_service: SummaryService,
    month: str,
    top: int,
) -> int:
    result = summary_service.monthly_summary(
        month,
        top,
    )

    if not result["has_data"]:
        print("[안내] 해당 월의 거래 데이터가 없습니다.")

    print(f"총 수입: {result['total_income']:,}원")
    print(f"총 지출: {result['total_expense']:,}원")
    print(f"잔액: {result['balance']:,}원")

    if result["budget"] is not None:
        print(
            f"예산: {result['budget']:,}원 "
            f"(사용률 {result['usage_rate']:.1f}%)"
        )

        if result["is_exceeded"]:
            print("[경고] 월 예산을 초과했습니다.")

    print()
    print(f"지출 TOP {top}")

    top_categories = result["top_categories"]

    if not top_categories:
        print("[안내] 지출 데이터가 없습니다.")
        return 0

    for index, item in enumerate(
        top_categories,
        start=1,
    ):
        category, amount = item
        print(f"{index}) {category}: {amount:,}원")

    return 0


# CLI 실행 중 발생하는 공통 오류는 데코레이터에서 처리합니다.
@handle_cli_errors
def main() -> int:
    # 명령어 파서를 생성하고 터미널 입력을 분석합니다.
    parser = build_parser()
    args: Any = parser.parse_args()

    # 사용자가 선택한 데이터 폴더를 기준으로 서비스 객체를 생성합니다.
    (
        transaction_service,
        category_service,
        budget_service,
        summary_service,
        csv_service,
    ) = create_services(args.data_dir)

    # ------------------------------------------------------------------
    # add
    # ------------------------------------------------------------------

    if args.command == "add":
        return run_add(transaction_service)

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------

    if args.command == "list":
        transactions = transaction_service.list_latest(
            args.limit
        )

        print_transactions(transactions)
        return 0

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------

    if args.command == "search":
        transactions = transaction_service.search(
            date_from=args.date_from,
            date_to=args.date_to,
            category=args.category,
            transaction_type=args.type,
            q=args.q,
            tag=args.tag,
        )

        print_transactions(transactions)
        return 0

    # ------------------------------------------------------------------
    # summary
    # ------------------------------------------------------------------

    if args.command == "summary":
        return run_summary(
            summary_service,
            args.month,
            args.top,
        )

    # ------------------------------------------------------------------
    # budget
    # ------------------------------------------------------------------

    if args.command == "budget":
        if args.budget_command == "set":
            budget = budget_service.set_budget(
                args.month,
                args.amount,
            )

            print(
                f"[저장 완료] {budget.month} 예산 "
                f"{budget.amount:,}원"
            )

            return 0

        if args.budget_command == "get":
            budget = budget_service.get_budget(
                args.month
            )

            if budget is None:
                print(
                    f"[안내] {args.month}에 설정된 "
                    "예산이 없습니다."
                )

            else:
                print(
                    f"{budget.month} 예산: "
                    f"{budget.amount:,}원"
                )

            return 0

    # ------------------------------------------------------------------
    # category
    # ------------------------------------------------------------------

    if args.command == "category":
        if args.category_command == "add":
            name = input(
                "카테고리명: "
            ).strip()

            created = category_service.add_category(
                name
            )

            if created:
                print(
                    f"[저장 완료] category="
                    f"{name.strip().lower()}"
                )

            else:
                print(
                    "[안내] 이미 존재하는 "
                    "카테고리입니다."
                )

            return 0

        if args.category_command == "list":
            categories = (
                category_service.list_categories()
            )

            if not categories:
                print(
                    "[안내] 등록된 카테고리가 없습니다."
                )
                return 0

            for category in categories:
                print(f"- {category}")

            return 0

        if args.category_command == "remove":
            removed = category_service.remove_category(
                args.name
            )

            if removed:
                print(
                    f"[삭제 완료] category="
                    f"{args.name.strip().lower()}"
                )

            else:
                print(
                    "[안내] 존재하지 않는 "
                    "카테고리입니다."
                )

            return 0

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------

    if args.command == "update":
        updated = transaction_service.update_transaction(
            transaction_id=args.id,
            date=args.date,
            transaction_type=args.type,
            category=args.category,
            amount=args.amount,
            memo=args.memo,
            tags_text=args.tags,
        )

        if updated:
            print(
                f"[수정 완료] id={args.id}"
            )

        else:
            print(
                "[안내] 해당 ID의 거래가 없습니다: "
                f"{args.id}"
            )

        return 0

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    if args.command == "delete":
        deleted = transaction_service.delete_transaction(
            args.id
        )

        if deleted:
            print(
                f"[삭제 완료] id={args.id}"
            )

        else:
            print(
                "[안내] 해당 ID의 거래가 없습니다: "
                f"{args.id}"
            )

        return 0

    # ------------------------------------------------------------------
    # import
    # ------------------------------------------------------------------

    if args.command == "import":
        imported, skipped, errors = (
            csv_service.import_csv(args.source)
        )

        for error in errors:
            print(
                f"[건너뜀] {error}"
            )

        print(
            f"[완료] imported={imported}, "
            f"skipped={skipped}"
        )

        return 0

    # ------------------------------------------------------------------
    # export
    # ------------------------------------------------------------------

    if args.command == "export":
        count = csv_service.export_csv(
            out=args.out,
            month=args.month,
            date_from=args.date_from,
            date_to=args.date_to,
        )

        print(
            f"[완료] {args.out} "
            f"({count} records)"
        )

        return 0

    # 정의되지 않은 명령어가 들어온 경우 argparse 오류를 발생시킵니다.
    parser.error("알 수 없는 명령입니다.")
    return 2