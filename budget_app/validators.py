# 사용자 입력값을 서비스 로직이나 파일 저장 단계로 넘기기 전에
# 날짜, 월, 금액, 거래 타입, 기간, 카테고리, 태그 형식이 올바른지 검사하고 정리하는 모듈.

# 문자열로 입력받은 날짜와 월이 올바른 형식인지 확인하기 위해
# datetime 클래스를 가져옵니다.
from datetime import datetime


# 날짜 문자열이 YYYY-MM-DD 형식인지 검사하는 함수입니다.
def validate_date(date_text: str) -> str:
    try:
        # 입력된 문자열을 YYYY-MM-DD 형식의 날짜로 변환해 봅니다.
        # 형식이 잘못되었거나 실제로 존재하지 않는 날짜라면
        # ValueError가 발생합니다.
        datetime.strptime(date_text, "%Y-%m-%d")

    except ValueError as exc:
        # 잘못된 날짜가 입력되면 사용자가 이해하기 쉬운
        # 새로운 오류 메시지를 발생시킵니다.
        raise ValueError(
            "날짜 형식이 올바르지 않습니다. 예: 2026-07-17"
        ) from exc

    # 검증에 성공한 날짜 문자열을 그대로 반환합니다.
    return date_text


# 월 문자열이 정확한 YYYY-MM 형식인지 검사하는 함수입니다.
def validate_month(month_text: str) -> str:
    try:
        # 입력된 문자열을 YYYY-MM 형식으로 변환합니다.
        # 변환된 datetime 객체를 parsed 변수에 저장합니다.
        parsed = datetime.strptime(month_text, "%Y-%m")

    except ValueError as exc:
        # 월 형식이 잘못되었으면 이해하기 쉬운 오류를 발생시킵니다.
        raise ValueError(
            "월 형식이 올바르지 않습니다. 예: 2026-07"
        ) from exc

    # strptime은 환경에 따라 "2026-7"처럼 월이 한 자리인 값도
    # 정상적으로 받아들일 수 있습니다.
    # 따라서 다시 YYYY-MM 형식으로 변환한 결과와
    # 원래 입력값을 비교하여 정확한 형식인지 확인합니다.
    if parsed.strftime("%Y-%m") != month_text:
        raise ValueError(
            "월 형식은 반드시 YYYY-MM이어야 합니다. 예: 2026-07"
        )

    # 검증에 성공한 월 문자열을 그대로 반환합니다.
    return month_text


# 금액이 0보다 큰 양수인지 검사하는 함수입니다.
def validate_amount(amount: int) -> int:
    # 금액이 0이거나 음수라면 사용할 수 없으므로 오류를 발생시킵니다.
    if amount <= 0:
        raise ValueError("금액은 0보다 큰 양수여야 합니다.")

    # 올바른 금액이면 그대로 반환합니다.
    return amount


# 거래 타입이 income 또는 expense인지 검사하는 함수입니다.
def validate_type(transaction_type: str) -> str:
    # 허용된 값의 집합 안에 입력값이 포함되어 있는지 확인합니다.
    if transaction_type not in {"income", "expense"}:
        raise ValueError(
            "거래 타입은 income 또는 expense만 가능합니다."
        )

    # 올바른 거래 타입이면 그대로 반환합니다.
    return transaction_type


# 검색 또는 내보내기에서 사용하는 시작 날짜와 종료 날짜를 검사합니다.
def validate_date_range(
    # 시작 날짜입니다.
    # 값이 없을 수도 있으므로 str 또는 None을 허용합니다.
    date_from: str | None,

    # 종료 날짜입니다.
    # 값이 없을 수도 있으므로 str 또는 None을 허용합니다.
    date_to: str | None,
) -> None:
    # 시작 날짜가 입력되었다면 날짜 형식을 검사합니다.
    if date_from is not None:
        validate_date(date_from)

    # 종료 날짜가 입력되었다면 날짜 형식을 검사합니다.
    if date_to is not None:
        validate_date(date_to)

    # 시작 날짜와 종료 날짜가 모두 입력된 경우,
    # 시작 날짜가 종료 날짜보다 늦지 않은지 확인합니다.
    #
    # YYYY-MM-DD 형식은 연도, 월, 일 순서로 되어 있기 때문에
    # 문자열 비교만으로도 날짜의 앞뒤 관계를 확인할 수 있습니다.
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise ValueError(
            "--from 날짜는 --to 날짜보다 늦을 수 없습니다."
        )


# --limit, --top처럼 반드시 양수여야 하는 옵션 값을 검사합니다.
def validate_positive_option(value: int, option_name: str) -> int:
    # 값이 0이거나 음수이면 잘못된 옵션으로 처리합니다.
    if value <= 0:
        # 어떤 옵션에서 문제가 생겼는지
        # option_name을 오류 메시지에 포함합니다.
        raise ValueError(f"{option_name}은 0보다 커야 합니다.")

    # 올바른 값이면 그대로 반환합니다.
    return value


# 카테고리 이름을 일정한 형식으로 정리하는 함수입니다.
def normalize_category(name: str) -> str:
    # 앞뒤 공백을 제거하고 모두 소문자로 변환합니다.
    #
    # 예:
    # "  Food  " → "food"
    normalized = name.strip().lower()

    # 공백 제거 후 아무 내용도 남지 않았다면
    # 빈 카테고리 이름이므로 오류를 발생시킵니다.
    if not normalized:
        raise ValueError("카테고리 이름은 비워둘 수 없습니다.")

    # 쉼표는 CSV나 여러 값 구분에 사용될 수 있으므로
    # 카테고리 이름 안에서는 허용하지 않습니다.
    if "," in normalized:
        raise ValueError("카테고리 이름에는 쉼표를 사용할 수 없습니다.")

    # 정리된 카테고리 이름을 반환합니다.
    return normalized


# 쉼표로 구분된 태그 문자열을 문자열 리스트로 변환합니다.
def parse_tags(tags_text: str) -> list[str]:
    # 입력값이 비어 있거나 공백만 있다면
    # 태그가 없는 것으로 보고 빈 리스트를 반환합니다.
    if not tags_text.strip():
        return []

    # 정리된 태그들을 저장할 빈 리스트를 만듭니다.
    tags: list[str] = []

    # 쉼표를 기준으로 태그 문자열을 나눕니다.
    #
    # 예:
    # "meal, school, daily"
    # → ["meal", " school", " daily"]
    for raw_tag in tags_text.split(","):
        # 각 태그의 앞뒤 공백을 제거하고 소문자로 변환합니다.
        tag = raw_tag.strip().lower()

        # 태그가 비어 있지 않고,
        # 이미 tags 리스트에 존재하지 않는 경우에만 추가합니다.
        #
        # 따라서 중복 태그는 한 번만 저장됩니다.
        if tag and tag not in tags:
            tags.append(tag)

    # 정리된 태그 리스트를 반환합니다.
    return tags