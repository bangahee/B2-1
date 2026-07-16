# format_transaction()
# → Transaction 객체 한 건을 보기 좋은 한 줄 문자열로 변환

# print_transactions()
# → 여러 거래를 반복해서 출력
# → 거래가 없으면 안내 메시지 출력



# 리스트뿐 아니라 튜플, 제너레이터 등
# 반복 가능한 여러 자료형을 타입으로 표현하기 위해 Iterable을 가져옵니다.
from collections.abc import Iterable

# 거래 한 건의 데이터 구조를 사용하기 위해
# models.py에서 Transaction 클래스를 가져옵니다.
from budget_app.models import Transaction


# Transaction 객체 한 건을
# 콘솔에 출력하기 좋은 문자열 형태로 변환하는 함수입니다.
def format_transaction(transaction: Transaction) -> str:
    # tags가 리스트라면 각 태그를 쉼표로 연결합니다.
    #
    # 예:
    # ["meal", "school"] → "meal,school"
    #
    # tags가 None이면 빈 리스트를 사용하므로
    # 결과는 빈 문자열이 됩니다.
    tags = ",".join(transaction.tags or [])

    # 거래 정보를 한 줄의 문자열로 만들어 반환합니다.
    return (
        # 거래 고유 ID를 출력합니다.
        f"{transaction.id} | "

        # 거래 날짜를 출력합니다.
        f"{transaction.date} | "

        # 거래 타입을 최소 7칸 너비로 왼쪽 정렬합니다.
        #
        # 예:
        # "income " 또는 "expense"
        f"{transaction.type:<7} | "

        # 카테고리를 최소 12칸 너비로 왼쪽 정렬합니다.
        f"{transaction.category:<12} | "

        # 금액을 최소 10칸 너비로 오른쪽 정렬합니다.
        f"{transaction.amount:>10} | "

        # 메모를 출력합니다.
        f"{transaction.memo} | "

        # 쉼표로 연결된 태그 문자열을 출력합니다.
        f"{tags}"
    )


# 여러 개의 Transaction 객체를 콘솔에 출력하는 함수입니다.
def print_transactions(
    # Iterable을 사용했기 때문에 리스트뿐 아니라
    # 튜플이나 제너레이터도 전달할 수 있습니다.
    transactions: Iterable[Transaction],
) -> None:
    # 거래가 한 건이라도 출력되었는지 확인하기 위한 변수입니다.
    printed = False

    # 전달받은 거래들을 한 건씩 반복합니다.
    for transaction in transactions:
        # 각 Transaction 객체를 문자열로 변환한 뒤 출력합니다.
        print(format_transaction(transaction))

        # 거래가 한 건 이상 출력되었음을 표시합니다.
        printed = True

    # 반복문에서 아무 거래도 출력되지 않았다면
    # 검색 조건에 맞는 데이터가 없다는 안내 메시지를 출력합니다.
    if not printed:
        print("[안내] 조건에 맞는 거래 내역이 없습니다.")