import argparse

from budget_app.decorators import handle_cli_errors
from budget_app.formatters import print_transactions
from budget_app.repositories import (
    DataPaths,
    TransactionRepository,
    CategoryRepository,
    BudgetRepository,
)
from budget_app.services import (
    TransactionService,
    CategoryService,
    BudgetService,
    SummaryService,
    CsvService,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="File-based household budget console app"
    )

    parser.add_argument("--data-dir", default="data", help="Data directory path")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("add", help="Add a new transaction")

    list_parser = subparsers.add_parser("list", help="List transactions")
    list_parser.add_argument("--limit", type=int, default=10)

    search_parser = subparsers.add_parser("search", help="Search transactions")
    search_parser.add_argument("--from", dest="date_from")
    search_parser.add_argument("--to", dest="date_to")
    search_parser.add_argument("--category")
    search_parser.add_argument("--type", choices=["income", "expense"])
    search_parser.add_argument("--q")
    search_parser.add_argument("--tag")

    summary_parser = subparsers.add_parser("summary", help="Show monthly summary")
    summary_parser.add_argument("--month", required=True)
    summary_parser.add_argument("--top", type=int, default=3)

    budget_parser = subparsers.add_parser("budget", help="Manage budget")
    budget_subparsers = budget_parser.add_subparsers(dest="budget_command")
    budget_set = budget_subparsers.add_parser("set", help="Set monthly budget")
    budget_set.add_argument("--month", required=True)
    budget_set.add_argument("--amount", type=int, required=True)

    category_parser = subparsers.add_parser("category", help="Manage categories")
    category_subparsers = category_parser.add_subparsers(dest="category_command")
    category_subparsers.add_parser("add", help="Add category")
    category_subparsers.add_parser("list", help="List categories")
    category_remove = category_subparsers.add_parser("remove", help="Remove category")
    category_remove.add_argument("--name", required=True)

    update_parser = subparsers.add_parser("update", help="Update transaction")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--date")
    update_parser.add_argument("--type", choices=["income", "expense"])
    update_parser.add_argument("--category")
    update_parser.add_argument("--amount", type=int)
    update_parser.add_argument("--memo")
    update_parser.add_argument("--tags")

    delete_parser = subparsers.add_parser("delete", help="Delete transaction")
    delete_parser.add_argument("--id", required=True)

    import_parser = subparsers.add_parser("import", help="Import transactions from CSV")
    import_parser.add_argument("--from", dest="source", required=True)

    export_parser = subparsers.add_parser("export", help="Export transactions to CSV")
    export_parser.add_argument("--out", required=True)
    export_parser.add_argument("--month")
    export_parser.add_argument("--from", dest="date_from")
    export_parser.add_argument("--to", dest="date_to")

    return parser


def create_services(data_dir: str):
    paths = DataPaths(data_dir)
    paths.ensure_files()

    transaction_repo = TransactionRepository(paths)
    category_repo = CategoryRepository(paths)
    budget_repo = BudgetRepository(paths)

    transaction_service = TransactionService(transaction_repo, category_repo)
    category_service = CategoryService(category_repo, transaction_repo)
    budget_service = BudgetService(budget_repo)
    summary_service = SummaryService(transaction_repo, budget_repo)
    csv_service = CsvService(transaction_service, transaction_repo, category_repo)

    return (
        transaction_service,
        category_service,
        budget_service,
        summary_service,
        csv_service,
    )


@handle_cli_errors
def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    (
        transaction_service,
        category_service,
        budget_service,
        summary_service,
        csv_service,
    ) = create_services(args.data_dir)

    if args.command == "add":
        date = input("날짜(YYYY-MM-DD): ").strip()
        transaction_type = input("타입(income/expense): ").strip()
        category = input("카테고리: ").strip()
        amount = int(input("금액(양수): ").strip())
        memo = input("메모(선택): ").strip()
        tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

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

    if args.command == "list":
        transactions = transaction_service.list_latest(args.limit)
        print_transactions(transactions)
        return 0

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

    if args.command == "summary":
        result = summary_service.monthly_summary(args.month, args.top)

        if not result["has_data"]:
            print("[안내] 해당 월의 데이터가 없습니다.")
            return 0

        print(f"총 수입: {result['total_income']}원")
        print(f"총 지출: {result['total_expense']}원")
        print(f"잔액: {result['balance']}원")

        if result["budget"] is not None:
            print(f"예산: {result['budget']}원 (사용률 {result['usage_rate']:.1f}%)")
            if result["is_exceeded"]:
                print("[경고] 예산을 초과했습니다.")

        print()
        print(f"지출 TOP {args.top}")

        top_categories = result["top_categories"]
        if not top_categories:
            print("[안내] 지출 데이터가 없습니다.")
        else:
            for index, (category, amount) in enumerate(top_categories, start=1):
                print(f"{index}) {category} {amount}원")

        return 0

    if args.command == "budget":
        if args.budget_command == "set":
            budget = budget_service.set_budget(args.month, args.amount)
            print(f"[저장 완료] {budget.month} 예산 {budget.amount}원")
            return 0

        print("[오류] budget 하위 명령이 필요합니다.")
        return 1

    if args.command == "category":
        if args.category_command == "add":
            name = input("카테고리명: ").strip()
            created = category_service.add_category(name)

            if created:
                print(f"[저장 완료] category={name}")
            else:
                print(f"[안내] 이미 존재하는 카테고리입니다: {name}")
            return 0

        if args.category_command == "list":
            categories = category_service.list_categories()
            for category in categories:
                print(f"- {category}")
            return 0

        if args.category_command == "remove":
            removed = category_service.remove_category(args.name)

            if removed:
                print(f"[삭제 완료] category={args.name}")
            else:
                print(f"[안내] 존재하지 않는 카테고리입니다: {args.name}")
            return 0

        print("[오류] category 하위 명령이 필요합니다.")
        return 1

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
            print(f"[수정 완료] id={args.id}")
        else:
            print(f"[안내] 해당 id의 거래가 없습니다: {args.id}")
        return 0

    if args.command == "delete":
        deleted = transaction_service.delete_transaction(args.id)

        if deleted:
            print(f"[삭제 완료] id={args.id}")
        else:
            print(f"[안내] 해당 id의 거래가 없습니다: {args.id}")
        return 0

    if args.command == "import":
        imported, skipped = csv_service.import_csv(args.source)
        print(f"[완료] imported={imported}, skipped={skipped}")
        return 0

    if args.command == "export":
        count = csv_service.export_csv(
            out=args.out,
            month=args.month,
            date_from=args.date_from,
            date_to=args.date_to,
        )
        print(f"[완료] {args.out} ({count} records)")
        return 0

    print("[오류] 알 수 없는 명령입니다.")
    return 1