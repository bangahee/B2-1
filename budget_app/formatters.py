from budget_app.models import Transaction


def format_transaction(transaction: Transaction) -> str:
    tags = ",".join(transaction.tags or [])
    return (
        f"{transaction.id} | "
        f"{transaction.date} | "
        f"{transaction.type:<7} | "
        f"{transaction.category:<10} | "
        f"{transaction.amount} | "
        f"{transaction.memo} | "
        f"{tags}"
    )


def print_transactions(transactions: list[Transaction]) -> None:
    if not transactions:
        print("[안내] 거래 내역이 없습니다.")
        return

    for transaction in transactions:
        print(format_transaction(transaction))