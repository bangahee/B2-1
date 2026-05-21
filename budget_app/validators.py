from datetime import datetime


def validate_date(date_text: str) -> str:
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("날짜 형식이 올바르지 않습니다. 예: 2024-01-15") from exc
    return date_text


def validate_month(month_text: str) -> str:
    try:
        datetime.strptime(month_text, "%Y-%m")
    except ValueError as exc:
        raise ValueError("월 형식이 올바르지 않습니다. 예: 2024-01") from exc
    return month_text


def validate_amount(amount: int) -> int:
    if amount <= 0:
        raise ValueError("금액은 양수여야 합니다.")
    return amount


def validate_type(transaction_type: str) -> str:
    if transaction_type not in {"income", "expense"}:
        raise ValueError("type은 income 또는 expense만 가능합니다.")
    return transaction_type


def parse_tags(tags_text: str) -> list[str]:
    if not tags_text.strip():
        return []
    return [tag.strip() for tag in tags_text.split(",") if tag.strip()]