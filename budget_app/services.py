import csv
from collections import defaultdict
from typing import Iterable

from budget_app.models import Transaction, Budget
from budget_app.repositories import TransactionRepository, CategoryRepository, BudgetRepository
from budget_app.validators import (
    validate_date,
    validate_month,
    validate_amount,
    validate_type,
    parse_tags,
)


class CategoryService:
    def __init__(
        self,
        category_repo: CategoryRepository,
        transaction_repo: TransactionRepository,
    ) -> None:
        self.category_repo = category_repo
        self.transaction_repo = transaction_repo

    def add_category(self, name: str) -> bool:
        name = name.strip()
        if not name:
            raise ValueError("카테고리 이름은 비워둘 수 없습니다.")
        return self.category_repo.add(name)

    def list_categories(self) -> list[str]:
        return self.category_repo.list_categories()

    def remove_category(self, name: str) -> bool:
        for transaction in self.transaction_repo.iter_transactions():
            if transaction.category == name:
                raise ValueError("이미 사용 중인 카테고리는 삭제할 수 없습니다.")
        return self.category_repo.remove(name)


class TransactionService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        category_repo: CategoryRepository,
    ) -> None:
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo

    def add_transaction(
        self,
        date: str,
        transaction_type: str,
        category: str,
        amount: int,
        memo: str,
        tags_text: str,
    ) -> Transaction:
        validate_date(date)
        validate_type(transaction_type)
        validate_amount(amount)

        if not self.category_repo.exists(category):
            raise ValueError(f"존재하지 않는 카테고리입니다: {category}")

        transaction = Transaction(
            id=self.transaction_repo.get_next_id(),
            date=date,
            type=transaction_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=parse_tags(tags_text),
        )

        self.transaction_repo.add(transaction)
        return transaction

    def list_latest(self, limit: int) -> list[Transaction]:
        if limit <= 0:
            raise ValueError("--limit은 양수여야 합니다.")

        transactions = list(self.transaction_repo.iter_transactions())
        transactions.sort(key=lambda x: x.date, reverse=True)
        return transactions[:limit]

    def search(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        q: str | None = None,
        tag: str | None = None,
    ) -> list[Transaction]:
        if date_from:
            validate_date(date_from)
        if date_to:
            validate_date(date_to)
        if transaction_type:
            validate_type(transaction_type)

        results: list[Transaction] = []

        for transaction in self.transaction_repo.iter_transactions():
            if date_from and transaction.date < date_from:
                continue
            if date_to and transaction.date > date_to:
                continue
            if category and transaction.category != category:
                continue
            if transaction_type and transaction.type != transaction_type:
                continue
            if q and q.lower() not in transaction.memo.lower():
                continue
            if tag and tag not in (transaction.tags or []):
                continue

            results.append(transaction)

        results.sort(key=lambda x: x.date, reverse=True)
        return results

    def update_transaction(
        self,
        transaction_id: str,
        date: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        amount: int | None = None,
        memo: str | None = None,
        tags_text: str | None = None,
    ) -> bool:
        updated = False
        new_transactions: list[Transaction] = []

        for transaction in self.transaction_repo.iter_transactions():
            if transaction.id == transaction_id:
                updated = True

                if date is not None:
                    validate_date(date)
                    transaction.date = date

                if transaction_type is not None:
                    validate_type(transaction_type)
                    transaction.type = transaction_type

                if category is not None:
                    if not self.category_repo.exists(category):
                        raise ValueError(f"존재하지 않는 카테고리입니다: {category}")
                    transaction.category = category

                if amount is not None:
                    validate_amount(amount)
                    transaction.amount = amount

                if memo is not None:
                    transaction.memo = memo

                if tags_text is not None:
                    transaction.tags = parse_tags(tags_text)

            new_transactions.append(transaction)

        if updated:
            self.transaction_repo.rewrite_all(new_transactions)

        return updated

    def delete_transaction(self, transaction_id: str) -> bool:
        deleted = False
        new_transactions: list[Transaction] = []

        for transaction in self.transaction_repo.iter_transactions():
            if transaction.id == transaction_id:
                deleted = True
                continue
            new_transactions.append(transaction)

        if deleted:
            self.transaction_repo.rewrite_all(new_transactions)

        return deleted


class BudgetService:
    def __init__(self, budget_repo: BudgetRepository) -> None:
        self.budget_repo = budget_repo

    def set_budget(self, month: str, amount: int) -> Budget:
        validate_month(month)
        validate_amount(amount)

        budget = Budget(month=month, amount=amount)
        self.budget_repo.set(budget)
        return budget

    def get_budget(self, month: str) -> Budget | None:
        validate_month(month)
        return self.budget_repo.get(month)


class SummaryService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
    ) -> None:
        self.transaction_repo = transaction_repo
        self.budget_repo = budget_repo

    def monthly_summary(self, month: str, top: int) -> dict[str, object]:
        validate_month(month)

        total_income = 0
        total_expense = 0
        category_expenses: dict[str, int] = defaultdict(int)

        for transaction in self.transaction_repo.iter_transactions():
            if not transaction.date.startswith(month):
                continue

            if transaction.type == "income":
                total_income += transaction.amount
            elif transaction.type == "expense":
                total_expense += transaction.amount
                category_expenses[transaction.category] += transaction.amount

        top_categories = sorted(
            category_expenses.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:top]

        budget = self.budget_repo.get(month)
        usage_rate = None
        is_exceeded = False

        if budget:
            usage_rate = total_expense / budget.amount * 100
            is_exceeded = total_expense > budget.amount

        return {
            "month": month,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
            "budget": budget.amount if budget else None,
            "usage_rate": usage_rate,
            "is_exceeded": is_exceeded,
            "has_data": total_income > 0 or total_expense > 0,
        }


class CsvService:
    def __init__(
        self,
        transaction_service: TransactionService,
        transaction_repo: TransactionRepository,
        category_repo: CategoryRepository,
    ) -> None:
        self.transaction_service = transaction_service
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo

    def import_csv(self, source: str) -> tuple[int, int]:
        imported = 0
        skipped = 0

        with open(source, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    self.transaction_service.add_transaction(
                        date=row["date"],
                        transaction_type=row["type"],
                        category=row["category"],
                        amount=int(row["amount"]),
                        memo=row.get("memo", ""),
                        tags_text=row.get("tags", ""),
                    )
                    imported += 1
                except Exception:
                    skipped += 1

        return imported, skipped

    def export_csv(
        self,
        out: str,
        month: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        if not month and not date_from and not date_to:
            raise ValueError("export는 --month 또는 --from/--to 조건이 필요합니다.")

        if month:
            validate_month(month)
        if date_from:
            validate_date(date_from)
        if date_to:
            validate_date(date_to)

        count = 0

        with open(out, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["date", "type", "category", "amount", "memo", "tags"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for transaction in self.transaction_repo.iter_transactions():
                if month and not transaction.date.startswith(month):
                    continue
                if date_from and transaction.date < date_from:
                    continue
                if date_to and transaction.date > date_to:
                    continue

                writer.writerow({
                    "date": transaction.date,
                    "type": transaction.type,
                    "category": transaction.category,
                    "amount": transaction.amount,
                    "memo": transaction.memo,
                    "tags": ",".join(transaction.tags or []),
                })
                count += 1

        return count