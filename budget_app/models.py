# 이 모듈은 거래 내역과 월별 예산의 데이터 구조를 정의하고,
# 객체와 JSONL 저장용 딕셔너리 사이의 변환을 담당합니다.



# dataclass를 만들기 위한 @dataclass와,
# dataclass 객체를 딕셔너리로 변환하는 asdict를 가져옵니다.
from dataclasses import asdict, dataclass

# 여러 종류의 값이 들어올 수 있음을 표현하기 위해 Any를 가져옵니다.
from typing import Any


# Transaction 클래스가 데이터를 저장하는 용도의 dataclass임을 나타냅니다.
@dataclass
class Transaction:
    # 거래의 고유 ID입니다.
    id: str

    # 거래 날짜입니다. 예: "2026-07-17"
    date: str

    # 거래 종류입니다. income 또는 expense를 사용합니다.
    type: str

    # 거래 카테고리입니다. 예: food, transport, salary
    category: str

    # 거래 금액입니다.
    amount: int

    # 선택 입력인 거래 메모입니다.
    # 입력하지 않으면 빈 문자열을 기본값으로 사용합니다.
    memo: str = ""

    # 선택 입력인 태그 목록입니다.
    # 태그가 없으면 None을 사용할 수 있습니다.
    tags: list[str] | None = None

    # Transaction 객체를 딕셔너리로 변환하는 메서드입니다.
    # JSONL 파일에 저장하기 전에 사용합니다.
    def to_dict(self) -> dict[str, Any]:
        # 현재 Transaction 객체의 모든 필드를 딕셔너리로 변환합니다.
        data = asdict(self)

        # tags가 None이면 저장할 때 빈 리스트로 변경합니다.
        # 이렇게 하면 JSON 파일 안에서 tags 형식을 항상 리스트로 유지할 수 있습니다.
        if data["tags"] is None:
            data["tags"] = []

        # 변환된 딕셔너리를 반환합니다.
        return data

    # 클래스 자체를 통해 호출할 수 있는 클래스 메서드입니다.
    # 딕셔너리 데이터를 Transaction 객체로 다시 변환할 때 사용합니다.
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        # 전달받은 딕셔너리의 값을 이용해
        # 새로운 Transaction 객체를 생성하고 반환합니다.
        return cls(
            # 각 값의 타입을 명확하게 맞추기 위해 str 또는 int로 변환합니다.
            id=str(data["id"]),
            date=str(data["date"]),
            type=str(data["type"]),
            category=str(data["category"]),
            amount=int(data["amount"]),

            # memo 값이 없으면 빈 문자열을 기본값으로 사용합니다.
            memo=str(data.get("memo", "")),

            # tags 값이 없으면 빈 리스트를 사용합니다.
            # 리스트 안의 각 태그도 문자열로 변환합니다.
            tags=[str(tag) for tag in data.get("tags", [])],
        )


# Budget 클래스도 데이터를 저장하기 위한 dataclass입니다.
@dataclass
class Budget:
    # 예산이 적용되는 월입니다. 예: "2026-07"
    month: str

    # 해당 월의 예산 금액입니다.
    amount: int

    # Budget 객체를 딕셔너리로 변환하는 메서드입니다.
    # JSONL 파일에 저장할 때 사용합니다.
    def to_dict(self) -> dict[str, Any]:
        # 현재 Budget 객체의 모든 필드를 딕셔너리로 변환해 반환합니다.
        return asdict(self)

    # 딕셔너리 데이터를 Budget 객체로 변환하는 클래스 메서드입니다.
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Budget":
        # 전달받은 month와 amount 값을 사용해
        # 새로운 Budget 객체를 생성하고 반환합니다.
        return cls(
            month=str(data["month"]),
            amount=int(data["amount"]),
        )