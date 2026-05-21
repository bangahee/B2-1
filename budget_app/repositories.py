import json
import os
from pathlib import Path
from typing import Iterator, Any

from budget_app.models import Transaction, Budget


DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary", "etc"]


class DataPaths:
    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.transactions = self.data_dir / "transactions.jsonl"
        self.categories = self.data_dir / "categories.jsonl"
        self.budgets = self.data_dir / "budgets.jsonl"

    def ensure_files(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

        for path in [self.transactions, self.categories, self.budgets]:
            if not path.exists():
                path.touch()

        if self.categories.stat().st_size == 0:
            with self.categories.open("w", encoding="utf-8") as f:
                for category in DEFAULT_CATEGORIES:
                    f.write(json.dumps({"name": category}, ensure_ascii=False) + "\n")


class TransactionRepository:
    def __init__(self, paths: DataPaths) -> None:
        self.paths = paths

    def iter_transactions(self) -> Iterator[Transaction]:
        with self.paths.transactions.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    yield Transaction.from_dict(data)

    def add(self, transaction: Transaction) -> None:
        with self.paths.transactions.open("a", encoding="utf-8") as f:
            f.write(json.dumps(transaction.to_dict(), ensure_ascii=False) + "\n")

    def get_next_id(self) -> str:
        max_num = 0
        for transaction in self.iter_transactions():
            try:
                number = int(transaction.id.replace("TX-", ""))
                max_num = max(max_num, number)
            except ValueError:
                continue
        return f"TX-{max_num + 1:06d}"

    def rewrite_all(self, transactions: list[Transaction]) -> None:
        temp_path = self.paths.transactions.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as f:
            for transaction in transactions:
                f.write(json.dumps(transaction.to_dict(), ensure_ascii=False) + "\n")

        os.replace(temp_path, self.paths.transactions)


class CategoryRepository:
    def __init__(self, paths: DataPaths) -> None:
        self.paths = paths

    def list_categories(self) -> list[str]:
        categories: list[str] = []
        with self.paths.categories.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    categories.append(str(data["name"]))
        return categories

    def exists(self, name: str) -> bool:
        return name in self.list_categories()

    def add(self, name: str) -> bool:
        if self.exists(name):
            return False

        with self.paths.categories.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"name": name}, ensure_ascii=False) + "\n")
        return True

    def remove(self, name: str) -> bool:
        categories = self.list_categories()

        if name not in categories:
            return False

        categories = [category for category in categories if category != name]
        temp_path = self.paths.categories.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as f:
            for category in categories:
                f.write(json.dumps({"name": category}, ensure_ascii=False) + "\n")

        os.replace(temp_path, self.paths.categories)
        return True


class BudgetRepository:
    def __init__(self, paths: DataPaths) -> None:
        self.paths = paths

    def iter_budgets(self) -> Iterator[Budget]:
        with self.paths.budgets.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield Budget.from_dict(json.loads(line))

    def get(self, month: str) -> Budget | None:
        for budget in self.iter_budgets():
            if budget.month == month:
                return budget
        return None

    def set(self, budget: Budget) -> None:
        budgets = [b for b in self.iter_budgets() if b.month != budget.month]
        budgets.append(budget)

        temp_path = self.paths.budgets.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as f:
            for item in budgets:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

        os.replace(temp_path, self.paths.budgets)