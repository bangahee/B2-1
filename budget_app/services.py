# CategoryService
# → 카테고리 추가, 조회, 삭제 규칙

# TransactionService
# → 거래 추가, 목록, 검색, 수정, 삭제

# BudgetService
# → 월별 예산 저장 및 조회

# SummaryService
# → 월별 총수입, 총지출, 잔액, 지출 TOP N 계산

# CsvService
# → CSV 가져오기 및 내보내기



# CSV 파일을 읽고 쓰기 위해 csv 모듈을 가져옵니다.
import csv

# 최신 거래 일부만 효율적으로 선택하기 위해 heapq를 가져옵니다.
import heapq

# 카테고리별 지출 합계를 쉽게 누적하기 위해 defaultdict를 가져옵니다.
from collections import defaultdict

# 제너레이터 반환 타입을 표현하기 위해 Iterator를 가져옵니다.
from collections.abc import Iterator

# 파일 경로를 운영체제와 관계없이 다루기 위해 Path를 가져옵니다.
from pathlib import Path

# 거래와 예산 데이터 모델을 가져옵니다.
from budget_app.models import Budget, Transaction

# 실제 JSONL 파일을 읽고 쓰는 저장소 클래스들을 가져옵니다.
from budget_app.repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)

# 입력값 검증과 데이터 정리를 담당하는 함수들을 가져옵니다.
from budget_app.validators import (
    normalize_category,
    parse_tags,
    validate_amount,
    validate_date,
    validate_date_range,
    validate_month,
    validate_positive_option,
    validate_type,
)


# 카테고리와 관련된 비즈니스 로직을 담당하는 서비스 클래스입니다.
class CategoryService:
    def __init__(
        self,
        category_repo: CategoryRepository,
        transaction_repo: TransactionRepository,
    ) -> None:
        # 카테고리 파일 저장소를 보관합니다.
        self.category_repo = category_repo

        # 사용 중인 카테고리인지 확인하기 위해 거래 저장소도 보관합니다.
        self.transaction_repo = transaction_repo

    # 새로운 카테고리를 추가합니다.
    def add_category(self, name: str) -> bool:
        # 카테고리 이름의 공백을 제거하고 소문자로 통일합니다.
        normalized = normalize_category(name)

        # 저장소에 카테고리를 추가합니다.
        # 성공하면 True, 이미 존재하면 False를 반환합니다.
        return self.category_repo.add(normalized)

    # 모든 카테고리를 정렬된 리스트로 반환합니다.
    def list_categories(self) -> list[str]:
        # 저장소에서 카테고리를 불러온 뒤 알파벳순으로 정렬합니다.
        return sorted(self.category_repo.list_categories())

    # 특정 카테고리를 삭제합니다.
    def remove_category(self, name: str) -> bool:
        # 입력받은 카테고리 이름을 정리합니다.
        normalized = normalize_category(name)

        # 모든 거래를 한 건씩 확인합니다.
        for transaction in self.transaction_repo.iter_transactions():
            # 삭제하려는 카테고리가 거래에서 사용 중이라면
            # 데이터 무결성을 위해 삭제를 막습니다.
            if transaction.category == normalized:
                raise ValueError(
                    "이미 거래에서 사용 중인 카테고리는 "
                    "삭제할 수 없습니다."
                )

        # 사용 중이 아니라면 카테고리 저장소에서 삭제합니다.
        return self.category_repo.remove(normalized)


# 거래 추가, 목록, 검색, 수정, 삭제 로직을 담당하는 서비스 클래스입니다.
class TransactionService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        category_repo: CategoryRepository,
    ) -> None:
        # 거래 파일 저장소를 보관합니다.
        self.transaction_repo = transaction_repo

        # 거래 추가 및 수정 시 카테고리 존재 여부를 확인하기 위해
        # 카테고리 저장소를 보관합니다.
        self.category_repo = category_repo

    # 객체 상태를 사용하지 않는 보조 함수이므로 staticmethod로 정의합니다.
    @staticmethod
    def latest_key(
        transaction: Transaction,
    ) -> tuple[str, str]:
        # 거래를 최신순으로 정렬할 때 사용할 기준을 반환합니다.
        # 먼저 날짜를 비교하고, 날짜가 같으면 거래 ID를 비교합니다.
        return transaction.date, transaction.id

    # 새로운 거래를 추가합니다.
    def add_transaction(
        self,
        date: str,
        transaction_type: str,
        category: str,
        amount: int,
        memo: str = "",
        tags_text: str = "",
    ) -> Transaction:
        # 날짜 형식을 검사합니다.
        validate_date(date)

        # 거래 타입이 income 또는 expense인지 검사합니다.
        validate_type(transaction_type)

        # 금액이 0보다 큰 양수인지 검사합니다.
        validate_amount(amount)

        # 카테고리 이름의 공백을 제거하고 소문자로 통일합니다.
        normalized_category = normalize_category(category)

        # 등록되지 않은 카테고리라면 거래를 추가하지 않습니다.
        if not self.category_repo.exists(normalized_category):
            raise ValueError(
                "존재하지 않는 카테고리입니다: "
                f"{normalized_category}"
            )

        # 검증이 끝난 값을 이용해 Transaction 객체를 생성합니다.
        transaction = Transaction(
            # 현재 저장된 거래를 기준으로 다음 고유 ID를 생성합니다.
            id=self.transaction_repo.get_next_id(),

            date=date,
            type=transaction_type,
            category=normalized_category,
            amount=amount,

            # 메모의 앞뒤 공백을 제거합니다.
            memo=memo.strip(),

            # 쉼표로 구분된 태그 문자열을 리스트로 변환합니다.
            tags=parse_tags(tags_text),
        )

        # 거래 객체를 JSONL 파일에 저장합니다.
        self.transaction_repo.add(transaction)

        # 생성된 거래 객체를 반환합니다.
        return transaction

    # 최신 거래를 지정한 개수만큼 반환합니다.
    def list_latest(self, limit: int) -> list[Transaction]:
        # limit 값이 0보다 큰지 검사합니다.
        validate_positive_option(limit, "--limit")

        # 전체 거래를 리스트로 한꺼번에 만든 뒤 정렬하지 않고,
        # heapq.nlargest를 사용하여 최신 거래 limit개만 선택합니다.
        return heapq.nlargest(
            limit,
            self.transaction_repo.iter_transactions(),
            key=self.latest_key,
        )

    # 검색 조건에 맞는 거래를 한 건씩 반환하는 제너레이터입니다.
    def iter_matching_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        q: str | None = None,
        tag: str | None = None,
    ) -> Iterator[Transaction]:
        # 시작 날짜와 종료 날짜의 형식 및 순서를 검사합니다.
        validate_date_range(date_from, date_to)

        # 거래 타입이 입력된 경우 올바른 값인지 검사합니다.
        if transaction_type is not None:
            validate_type(transaction_type)

        # 카테고리 검색 조건이 있다면 이름을 정리합니다.
        normalized_category = (
            normalize_category(category)
            if category is not None
            else None
        )

        # 태그 검색 조건이 있다면 공백을 제거하고 소문자로 변환합니다.
        normalized_tag = (
            tag.strip().lower()
            if tag is not None
            else None
        )

        # 메모 검색어가 있다면 공백을 제거하고 소문자로 변환합니다.
        normalized_query = (
            q.strip().lower()
            if q is not None
            else None
        )

        # 거래 파일을 한 건씩 읽습니다.
        for transaction in self.transaction_repo.iter_transactions():
            # 시작 날짜보다 이전 거래는 건너뜁니다.
            if date_from and transaction.date < date_from:
                continue

            # 종료 날짜보다 이후 거래는 건너뜁니다.
            if date_to and transaction.date > date_to:
                continue

            # 카테고리 조건과 일치하지 않으면 건너뜁니다.
            if (
                normalized_category
                and transaction.category != normalized_category
            ):
                continue

            # 거래 타입 조건과 일치하지 않으면 건너뜁니다.
            if (
                transaction_type
                and transaction.type != transaction_type
            ):
                continue

            # 메모에 검색어가 포함되지 않으면 건너뜁니다.
            if (
                normalized_query
                and normalized_query not in transaction.memo.lower()
            ):
                continue

            # 거래 태그 목록에 검색 태그가 없다면 건너뜁니다.
            if (
                normalized_tag
                and normalized_tag not in (transaction.tags or [])
            ):
                continue

            # 모든 조건을 통과한 거래만 한 건씩 반환합니다.
            yield transaction

    # 검색 조건에 맞는 거래를 최신순 리스트로 반환합니다.
    def search(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        q: str | None = None,
        tag: str | None = None,
    ) -> list[Transaction]:
        # 제너레이터를 통해 검색 조건에 맞는 거래만 가져옵니다.
        matches = self.iter_matching_transactions(
            date_from=date_from,
            date_to=date_to,
            category=category,
            transaction_type=transaction_type,
            q=q,
            tag=tag,
        )

        # 검색 결과를 날짜와 ID 기준 최신순으로 정렬합니다.
        return sorted(
            matches,
            key=self.latest_key,
            reverse=True,
        )

    # 특정 ID의 거래 내용을 수정합니다.
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
        # 수정 가능한 모든 값을 하나의 튜플로 모읍니다.
        values = (
            date,
            transaction_type,
            category,
            amount,
            memo,
            tags_text,
        )

        # 수정할 항목이 하나도 입력되지 않았다면 오류를 발생시킵니다.
        if all(value is None for value in values):
            raise ValueError(
                "수정할 항목을 하나 이상 입력해야 합니다."
            )

        # 새로운 날짜가 입력되었다면 형식을 검사합니다.
        if date is not None:
            validate_date(date)

        # 새로운 거래 타입이 입력되었다면 검사합니다.
        if transaction_type is not None:
            validate_type(transaction_type)

        # 수정할 카테고리를 저장할 변수입니다.
        normalized_category: str | None = None

        # 새로운 카테고리가 입력된 경우 이름을 정리하고 존재 여부를 확인합니다.
        if category is not None:
            normalized_category = normalize_category(category)

            if not self.category_repo.exists(normalized_category):
                raise ValueError(
                    "존재하지 않는 카테고리입니다: "
                    f"{normalized_category}"
                )

        # 새로운 금액이 입력되었다면 양수인지 검사합니다.
        if amount is not None:
            validate_amount(amount)

        # 태그 수정값이 입력된 경우 리스트로 변환합니다.
        parsed_tags = (
            parse_tags(tags_text)
            if tags_text is not None
            else None
        )

        # 실제 Transaction 객체에 변경 내용을 적용하는 내부 함수입니다.
        def apply_update(
            transaction: Transaction,
        ) -> Transaction:
            # 각 값이 None이 아닐 때만 기존 값을 변경합니다.
            if date is not None:
                transaction.date = date

            if transaction_type is not None:
                transaction.type = transaction_type

            if normalized_category is not None:
                transaction.category = normalized_category

            if amount is not None:
                transaction.amount = amount

            if memo is not None:
                transaction.memo = memo.strip()

            if parsed_tags is not None:
                transaction.tags = parsed_tags

            # 수정된 Transaction 객체를 반환합니다.
            return transaction

        # 저장소의 안전한 임시 파일 교체 방식을 이용해 수정합니다.
        # 거래 ID가 존재하면 True, 없으면 False를 반환합니다.
        return self.transaction_repo.update_by_id(
            transaction_id,
            apply_update,
        )

    # 특정 ID의 거래를 삭제합니다.
    def delete_transaction(self, transaction_id: str) -> bool:
        # 저장소의 안전한 삭제 기능을 호출합니다.
        return self.transaction_repo.delete_by_id(
            transaction_id
        )


# 월별 예산 설정 및 조회를 담당하는 서비스 클래스입니다.
class BudgetService:
    def __init__(
        self,
        budget_repo: BudgetRepository,
    ) -> None:
        # 예산 저장소를 보관합니다.
        self.budget_repo = budget_repo

    # 특정 월의 예산을 설정합니다.
    def set_budget(self, month: str, amount: int) -> Budget:
        # 월 형식이 YYYY-MM인지 검사합니다.
        validate_month(month)

        # 예산 금액이 양수인지 검사합니다.
        validate_amount(amount)

        # 검증된 값으로 Budget 객체를 생성합니다.
        budget = Budget(month=month, amount=amount)

        # 예산 파일에 저장합니다.
        self.budget_repo.set(budget)

        # 저장된 Budget 객체를 반환합니다.
        return budget

    # 특정 월의 예산을 조회합니다.
    def get_budget(self, month: str) -> Budget | None:
        # 월 형식을 검사합니다.
        validate_month(month)

        # 해당 월의 예산이 있으면 Budget 객체를,
        # 없으면 None을 반환합니다.
        return self.budget_repo.get(month)


# 월별 수입, 지출, 잔액, 카테고리별 지출을 계산하는 서비스입니다.
class SummaryService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
    ) -> None:
        # 거래 저장소를 보관합니다.
        self.transaction_repo = transaction_repo

        # 예산 저장소를 보관합니다.
        self.budget_repo = budget_repo

    # 특정 월의 요약 정보를 계산합니다.
    def monthly_summary(
        self,
        month: str,
        top: int,
    ) -> dict[str, object]:
        # 월 형식을 검사합니다.
        validate_month(month)

        # top 값이 0보다 큰지 검사합니다.
        validate_positive_option(top, "--top")

        # 총수입을 저장할 변수입니다.
        total_income = 0

        # 총지출을 저장할 변수입니다.
        total_expense = 0

        # 해당 월에 거래가 몇 건 있는지 저장합니다.
        transaction_count = 0

        # 카테고리별 지출 합계를 저장합니다.
        # 존재하지 않는 키에 접근하면 자동으로 0부터 시작합니다.
        category_expenses: dict[str, int] = defaultdict(int)

        # 거래를 한 건씩 읽습니다.
        for transaction in self.transaction_repo.iter_transactions():
            # 요청한 월의 거래가 아니면 건너뜁니다.
            if not transaction.date.startswith(f"{month}-"):
                continue

            # 해당 월의 거래 수를 1 증가시킵니다.
            transaction_count += 1

            # 수입 거래이면 총수입에 더합니다.
            if transaction.type == "income":
                total_income += transaction.amount

            # 그 외 expense 거래이면 총지출과 카테고리별 지출에 더합니다.
            else:
                total_expense += transaction.amount
                category_expenses[
                    transaction.category
                ] += transaction.amount

        # 카테고리별 지출을 금액이 큰 순서대로 정렬합니다.
        # 금액이 같으면 카테고리 이름순으로 정렬합니다.
        # 이후 top개만 선택합니다.
        top_categories = sorted(
            category_expenses.items(),
            key=lambda item: (-item[1], item[0]),
        )[:top]

        # 해당 월에 설정된 예산을 조회합니다.
        budget = self.budget_repo.get(month)

        # 예산 사용률을 저장할 변수입니다.
        # 예산이 없다면 None 상태를 유지합니다.
        usage_rate: float | None = None

        # 예산 초과 여부를 저장합니다.
        is_exceeded = False

        # 예산이 설정되어 있다면 사용률과 초과 여부를 계산합니다.
        if budget is not None:
            usage_rate = total_expense / budget.amount * 100
            is_exceeded = total_expense > budget.amount

        # CLI에서 출력할 수 있도록 계산 결과를 딕셔너리로 반환합니다.
        return {
            "month": month,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
            "budget": budget.amount if budget else None,
            "usage_rate": usage_rate,
            "is_exceeded": is_exceeded,
            "has_data": transaction_count > 0,
        }


# CSV 파일 가져오기와 내보내기를 담당하는 서비스 클래스입니다.
class CsvService:
    # CSV import에서 반드시 존재해야 하는 필수 열입니다.
    REQUIRED_COLUMNS = {
        "date",
        "type",
        "category",
        "amount",
    }

    # CSV export 시 사용할 전체 열의 순서입니다.
    FIELDNAMES = [
        "date",
        "type",
        "category",
        "amount",
        "memo",
        "tags",
    ]

    def __init__(
        self,
        transaction_service: TransactionService,
        transaction_repo: TransactionRepository,
    ) -> None:
        # CSV의 각 행을 실제 거래로 추가하기 위해
        # TransactionService를 보관합니다.
        self.transaction_service = transaction_service

        # CSV export 시 거래를 읽기 위해 저장소를 보관합니다.
        self.transaction_repo = transaction_repo

    # CSV 파일을 읽어 거래를 일괄 등록합니다.
    def import_csv(
        self,
        source: str,
    ) -> tuple[int, int, list[str]]:
        # 문자열 경로를 Path 객체로 변환합니다.
        source_path = Path(source)

        # 입력한 경로가 실제 파일이 아니라면 오류를 발생시킵니다.
        if not source_path.is_file():
            raise FileNotFoundError(source)

        # 정상적으로 가져온 행의 개수입니다.
        imported = 0

        # 오류 때문에 건너뛴 행의 개수입니다.
        skipped = 0

        # 각 오류 행의 번호와 원인을 저장할 리스트입니다.
        errors: list[str] = []

        # utf-8-sig는 일반 UTF-8과 BOM이 포함된 UTF-8 파일을 모두 읽을 수 있습니다.
        with source_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            # 첫 번째 줄을 헤더로 사용하는 CSV 리더를 생성합니다.
            reader = csv.DictReader(file)

            # 헤더가 없으면 올바른 CSV 파일로 처리할 수 없습니다.
            if reader.fieldnames is None:
                raise ValueError(
                    "CSV 헤더가 없습니다."
                )

            # 헤더 이름의 앞뒤 공백을 제거하여 집합으로 만듭니다.
            normalized_headers = {
                header.strip()
                for header in reader.fieldnames
                if header is not None
            }

            # 필수 열 중 실제 헤더에 없는 열을 계산합니다.
            missing_columns = (
                self.REQUIRED_COLUMNS - normalized_headers
            )

            # 누락된 필수 열이 있다면 import 전체를 중단합니다.
            if missing_columns:
                # 누락된 열 이름을 정렬하여 문자열로 만듭니다.
                missing_text = ", ".join(
                    sorted(missing_columns)
                )

                raise ValueError(
                    "CSV 필수 열이 없습니다: "
                    f"{missing_text}"
                )

            # CSV의 데이터 행을 한 줄씩 읽습니다.
            # 첫 줄이 헤더이므로 실제 데이터 행 번호는 2부터 시작합니다.
            for row_number, row in enumerate(reader, start=2):
                try:
                    # amount 값을 가져옵니다.
                    amount_text = row.get("amount")

                    # amount 열의 값이 없다면 해당 행을 잘못된 데이터로 처리합니다.
                    if amount_text is None:
                        raise ValueError(
                            "amount 값이 없습니다."
                        )

                    # 기존 add 기능을 재사용하여
                    # 날짜, 타입, 카테고리, 금액 검증을 동일하게 적용합니다.
                    self.transaction_service.add_transaction(
                        date=(row.get("date") or "").strip(),
                        transaction_type=(
                            row.get("type") or ""
                        ).strip(),
                        category=(
                            row.get("category") or ""
                        ).strip(),
                        amount=int(amount_text.strip()),
                        memo=row.get("memo") or "",
                        tags_text=row.get("tags") or "",
                    )

                    # 정상적으로 저장되면 imported를 1 증가시킵니다.
                    imported += 1

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ) as exc:
                    # 특정 행에서 오류가 발생해도 전체 import는 중단하지 않습니다.
                    skipped += 1

                    # 행 번호와 오류 원인을 저장합니다.
                    errors.append(
                        f"{row_number}행: {exc}"
                    )

        # 정상 처리 건수, 건너뛴 건수, 오류 목록을 반환합니다.
        return imported, skipped, errors

    # 조건에 맞는 거래를 CSV 파일로 내보냅니다.
    def export_csv(
        self,
        out: str,
        month: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        # 월, 시작 날짜, 종료 날짜가 모두 없다면
        # 전체 데이터를 무조건 내보내는 것을 막습니다.
        if (
            month is None
            and date_from is None
            and date_to is None
        ):
            raise ValueError(
                "export에는 --month 또는 "
                "--from/--to 조건이 필요합니다."
            )

        # 월 조건이 있다면 YYYY-MM 형식인지 검사합니다.
        if month is not None:
            validate_month(month)

        # 날짜 범위의 형식과 앞뒤 순서를 검사합니다.
        validate_date_range(date_from, date_to)

        # 출력 경로를 Path 객체로 변환합니다.
        output_path = Path(out)

        # 출력 파일에 상위 폴더가 지정된 경우,
        # 폴더가 없다면 자동으로 생성합니다.
        if output_path.parent != Path("."):
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        # 내보낸 거래 개수를 저장합니다.
        count = 0

        # 출력 CSV 파일을 쓰기 모드로 엽니다.
        with output_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            # 정해진 열 이름으로 CSV 작성 객체를 생성합니다.
            writer = csv.DictWriter(
                file,
                fieldnames=self.FIELDNAMES,
            )

            # CSV 첫 줄에 헤더를 작성합니다.
            writer.writeheader()

            # 저장된 거래를 한 건씩 읽습니다.
            for transaction in (
                self.transaction_repo.iter_transactions()
            ):
                # 월 조건이 있고 해당 월의 거래가 아니면 건너뜁니다.
                if (
                    month
                    and not transaction.date.startswith(
                        f"{month}-"
                    )
                ):
                    continue

                # 시작 날짜보다 이전 거래이면 건너뜁니다.
                if (
                    date_from
                    and transaction.date < date_from
                ):
                    continue

                # 종료 날짜보다 이후 거래이면 건너뜁니다.
                if date_to and transaction.date > date_to:
                    continue

                # 조건을 통과한 거래를 CSV 한 행으로 기록합니다.
                writer.writerow(
                    {
                        "date": transaction.date,
                        "type": transaction.type,
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "memo": transaction.memo,

                        # 태그 리스트를 쉼표로 연결된 문자열로 변환합니다.
                        "tags": ",".join(
                            transaction.tags or []
                        ),
                    }
                )

                # 내보낸 거래 개수를 증가시킵니다.
                count += 1

        # 최종 내보낸 거래 수를 반환합니다.
        return count