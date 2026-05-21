from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Transaction:
    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data["tags"] is None:
            data["tags"] = []
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        return cls(
            id=str(data["id"]),
            date=str(data["date"]),
            type=str(data["type"]),
            category=str(data["category"]),
            amount=int(data["amount"]),
            memo=str(data.get("memo", "")),
            tags=list(data.get("tags", [])),
        )


@dataclass
class Budget:
    month: str
    amount: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Budget":
        return cls(
            month=str(data["month"]),
            amount=int(data["amount"]),
        )