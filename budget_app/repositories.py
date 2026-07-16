# DataPaths
# → 데이터 폴더와 세 개의 저장 파일 경로 관리

# TransactionRepository
# → 거래 추가, 조회, ID 생성, 수정, 삭제

# CategoryRepository
# → 카테고리 조회, 추가, 삭제

# BudgetRepository
# → 월별 예산 조회 및 저장



# JSONL 형식의 데이터를 읽고 쓰기 위해 json 모듈을 가져옵니다.
import json

# 임시 파일을 기존 파일로 안전하게 교체하기 위해 os 모듈을 가져옵니다.
import os

# Callable은 함수를 타입으로 표현할 때 사용하고,
# Iterator는 제너레이터가 반환하는 타입을 표현할 때 사용합니다.
from collections.abc import Callable, Iterator

# 운영체제와 관계없이 파일 및 폴더 경로를 다루기 위해 Path를 가져옵니다.
from pathlib import Path

# 딕셔너리 안에 다양한 타입의 값이 들어갈 수 있음을 표현하기 위해 Any를 가져옵니다.
from typing import Any

# 거래와 예산 데이터를 객체 형태로 다루기 위해
# models.py에서 Budget과 Transaction 클래스를 가져옵니다.
from budget_app.models import Budget, Transaction


# 프로그램이 처음 실행될 때 자동으로 생성할 기본 카테고리 목록입니다.
DEFAULT_CATEGORIES = [
    "food",
    "transport",
    "rent",
    "salary",
    "etc",
]


# 데이터 파일들의 경로를 한 곳에서 관리하는 클래스입니다.
class DataPaths:
    # data_dir의 기본값은 "data"입니다.
    # 사용자가 --data-dir 옵션을 입력하면 다른 폴더를 사용할 수도 있습니다.
    def __init__(self, data_dir: str = "data") -> None:
        # 문자열로 받은 폴더 경로를 Path 객체로 변환합니다.
        self.data_dir = Path(data_dir)

        # 거래 데이터를 저장할 파일 경로입니다.
        self.transactions = self.data_dir / "transactions.jsonl"

        # 카테고리 데이터를 저장할 파일 경로입니다.
        self.categories = self.data_dir / "categories.jsonl"

        # 월별 예산 데이터를 저장할 파일 경로입니다.
        self.budgets = self.data_dir / "budgets.jsonl"

    # 데이터 폴더와 필수 저장 파일이 존재하는지 확인하고,
    # 없으면 자동으로 생성하는 메서드입니다.
    def ensure_files(self) -> None:
        # 데이터 폴더가 없으면 생성합니다.
        # parents=True는 상위 폴더도 함께 만들 수 있게 하고,
        # exist_ok=True는 이미 폴더가 있어도 오류가 발생하지 않게 합니다.
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 세 개의 필수 데이터 파일을 하나씩 확인합니다.
        for path in (
            self.transactions,
            self.categories,
            self.budgets,
        ):
            # 파일이 존재하지 않는 경우 빈 파일을 생성합니다.
            if not path.exists():
                path.touch()

        # 카테고리 파일의 크기가 0바이트이면,
        # 아직 저장된 카테고리가 없다는 의미입니다.
        if self.categories.stat().st_size == 0:
            # 카테고리 파일을 쓰기 모드로 엽니다.
            with self.categories.open(
                "w",
                encoding="utf-8",
            ) as file:
                # 기본 카테고리를 한 개씩 저장합니다.
                for category in DEFAULT_CATEGORIES:
                    # 각 카테고리를 JSON 객체 형태로 만듭니다.
                    record = {"name": category}

                    # JSON 문자열로 변환한 뒤 한 줄에 하나씩 기록합니다.
                    # ensure_ascii=False는 한글이 유니코드 코드가 아니라
                    # 실제 한글로 저장되도록 합니다.
                    file.write(
                        json.dumps(
                            record,
                            ensure_ascii=False,
                        )
                        + "\n"
                    )


# 거래 데이터 파일을 읽고 쓰는 저장소 클래스입니다.
class TransactionRepository:
    # DataPaths 객체를 전달받아 거래 파일 경로를 사용할 수 있게 합니다.
    def __init__(self, paths: DataPaths) -> None:
        self.paths = paths

    # 거래 파일을 한 줄씩 읽어 Transaction 객체를 반환하는 제너레이터입니다.
    def iter_transactions(self) -> Iterator[Transaction]:
        # 거래 파일을 읽기 모드로 엽니다.
        with self.paths.transactions.open(
            "r",
            encoding="utf-8",
        ) as file:
            # enumerate를 사용하여 현재 줄 번호와 줄 내용을 함께 가져옵니다.
            # 줄 번호는 1부터 시작합니다.
            for line_number, line in enumerate(file, start=1):
                # 빈 줄이 있다면 건너뜁니다.
                if not line.strip():
                    continue

                try:
                    # JSON 문자열 한 줄을 파이썬 딕셔너리로 변환합니다.
                    data: dict[str, Any] = json.loads(line)

                    # 딕셔너리를 Transaction 객체로 변환한 뒤
                    # yield를 사용하여 한 건씩 반환합니다.
                    yield Transaction.from_dict(data)

                except (
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                    ValueError,
                ) as exc:
                    # JSON 형식이 잘못되었거나 필수 값이 빠진 경우,
                    # 어느 줄이 손상되었는지 알려주는 오류를 발생시킵니다.
                    raise ValueError(
                        "거래 저장 파일의 "
                        f"{line_number}번째 줄이 손상되었습니다."
                    ) from exc

    # 새로운 거래 한 건을 거래 파일 끝에 추가하는 메서드입니다.
    def add(self, transaction: Transaction) -> None:
        # append 모드인 "a"로 열기 때문에 기존 내용은 유지되고
        # 새로운 거래가 파일 끝에 추가됩니다.
        with self.paths.transactions.open(
            "a",
            encoding="utf-8",
        ) as file:
            # Transaction 객체를 딕셔너리로 변환하고,
            # 다시 JSON 문자열로 변환하여 한 줄로 저장합니다.
            file.write(
                json.dumps(
                    transaction.to_dict(),
                    ensure_ascii=False,
                )
                + "\n"
            )

    # 특정 거래 ID가 존재하는지 확인하는 메서드입니다.
    def exists(self, transaction_id: str) -> bool:
        # 거래를 한 건씩 읽으면서 ID가 같은 거래가 하나라도 있으면 True를 반환합니다.
        return any(
            transaction.id == transaction_id
            for transaction in self.iter_transactions()
        )

    # 다음 거래 ID를 생성하는 메서드입니다.
    def get_next_id(self) -> str:
        # 현재까지 발견한 가장 큰 거래 번호를 저장합니다.
        max_number = 0

        # 모든 거래를 한 건씩 읽습니다.
        for transaction in self.iter_transactions():
            # ID가 TX-로 시작하지 않으면 정상 거래 ID로 보지 않고 건너뜁니다.
            if not transaction.id.startswith("TX-"):
                continue

            try:
                # 예: "TX-000012"에서 "TX-"를 제거하고
                # 나머지 숫자를 정수로 변환합니다.
                number = int(transaction.id.removeprefix("TX-"))

            except ValueError:
                # 숫자로 변환할 수 없는 잘못된 ID라면 건너뜁니다.
                continue

            # 지금까지 발견한 번호 중 가장 큰 값을 저장합니다.
            max_number = max(max_number, number)

        # 가장 큰 번호에 1을 더해 새로운 ID를 만듭니다.
        # :06d는 숫자를 6자리로 맞추고 앞을 0으로 채웁니다.
        return f"TX-{max_number + 1:06d}"

    # 특정 ID의 거래를 수정하는 메서드입니다.
    def update_by_id(
        self,
        transaction_id: str,

        # updater는 Transaction 객체를 받아
        # 수정된 Transaction 객체를 반환하는 함수입니다.
        updater: Callable[[Transaction], Transaction],
    ) -> bool:
        # 기존 거래 파일과 같은 위치에 임시 파일 경로를 만듭니다.
        temp_path = self.paths.transactions.with_suffix(
            ".jsonl.tmp"
        )

        # 수정하려는 ID를 찾았는지 기록합니다.
        found = False

        try:
            # 임시 파일을 쓰기 모드로 엽니다.
            with temp_path.open(
                "w",
                encoding="utf-8",
            ) as output_file:
                # 기존 거래 파일을 한 건씩 읽습니다.
                for transaction in self.iter_transactions():
                    # 현재 거래의 ID가 수정 대상 ID와 같다면,
                    # 전달받은 updater 함수를 이용해 거래 내용을 수정합니다.
                    if transaction.id == transaction_id:
                        transaction = updater(transaction)
                        found = True

                    # 수정 여부와 관계없이 모든 거래를 임시 파일에 기록합니다.
                    output_file.write(
                        json.dumps(
                            transaction.to_dict(),
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

            # 수정 대상 거래를 찾았다면,
            # 임시 파일을 기존 거래 파일로 안전하게 교체합니다.
            if found:
                os.replace(
                    temp_path,
                    self.paths.transactions,
                )

            else:
                # 대상 ID가 없었다면 원본 파일을 교체하지 않고
                # 불필요한 임시 파일만 삭제합니다.
                temp_path.unlink(missing_ok=True)

            # 거래를 찾았는지 여부를 반환합니다.
            return found

        except Exception:
            # 파일 처리 중 오류가 발생한 경우,
            # 남아 있을 수 있는 임시 파일을 삭제합니다.
            temp_path.unlink(missing_ok=True)

            # 오류를 다시 상위 코드로 전달합니다.
            raise

    # 특정 ID의 거래를 삭제하는 메서드입니다.
    def delete_by_id(self, transaction_id: str) -> bool:
        # 삭제 결과를 기록할 임시 파일 경로를 만듭니다.
        temp_path = self.paths.transactions.with_suffix(
            ".jsonl.tmp"
        )

        # 삭제할 거래를 찾았는지 기록합니다.
        found = False

        try:
            # 임시 파일을 쓰기 모드로 엽니다.
            with temp_path.open(
                "w",
                encoding="utf-8",
            ) as output_file:
                # 기존 거래 파일을 한 건씩 읽습니다.
                for transaction in self.iter_transactions():
                    # 삭제 대상 ID와 같다면 임시 파일에 기록하지 않고 건너뜁니다.
                    if transaction.id == transaction_id:
                        found = True
                        continue

                    # 삭제 대상이 아닌 거래만 임시 파일에 기록합니다.
                    output_file.write(
                        json.dumps(
                            transaction.to_dict(),
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

            # 삭제 대상 거래가 존재했다면,
            # 임시 파일을 기존 거래 파일로 교체합니다.
            if found:
                os.replace(
                    temp_path,
                    self.paths.transactions,
                )

            else:
                # 삭제할 ID가 없었다면 원본 파일은 유지하고
                # 임시 파일만 삭제합니다.
                temp_path.unlink(missing_ok=True)

            # 삭제 성공 여부를 반환합니다.
            return found

        except Exception:
            # 오류 발생 시 임시 파일을 정리합니다.
            temp_path.unlink(missing_ok=True)

            # 오류를 상위 코드로 다시 전달합니다.
            raise


# 카테고리 데이터를 읽고 쓰는 저장소 클래스입니다.
class CategoryRepository:
    # DataPaths 객체를 전달받아 카테고리 파일 경로를 사용합니다.
    def __init__(self, paths: DataPaths) -> None:
        self.paths = paths

    # 카테고리 파일을 한 줄씩 읽어 카테고리 이름을 반환하는 제너레이터입니다.
    def iter_categories(self) -> Iterator[str]:
        # 카테고리 파일을 읽기 모드로 엽니다.
        with self.paths.categories.open(
            "r",
            encoding="utf-8",
        ) as file:
            # 줄 번호와 줄 내용을 함께 읽습니다.
            for line_number, line in enumerate(file, start=1):
                # 빈 줄은 건너뜁니다.
                if not line.strip():
                    continue

                try:
                    # JSON 문자열을 딕셔너리로 변환합니다.
                    data = json.loads(line)

                    # name 값을 문자열로 변환하여 한 개씩 반환합니다.
                    yield str(data["name"])

                except (
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                ) as exc:
                    # 파일 형식이 잘못된 경우 어느 줄인지 알려주는 오류를 발생시킵니다.
                    raise ValueError(
                        "카테고리 저장 파일의 "
                        f"{line_number}번째 줄이 손상되었습니다."
                    ) from exc

    # 모든 카테고리를 리스트로 반환하는 메서드입니다.
    def list_categories(self) -> list[str]:
        # 카테고리 제너레이터의 결과를 리스트로 변환합니다.
        return list(self.iter_categories())

    # 특정 카테고리가 존재하는지 확인합니다.
    def exists(self, name: str) -> bool:
        # 같은 이름의 카테고리가 하나라도 있으면 True를 반환합니다.
        return any(
            category == name
            for category in self.iter_categories()
        )

    # 새로운 카테고리를 추가하는 메서드입니다.
    def add(self, name: str) -> bool:
        # 이미 같은 이름의 카테고리가 있으면 추가하지 않고 False를 반환합니다.
        if self.exists(name):
            return False

        # 카테고리 파일을 append 모드로 엽니다.
        with self.paths.categories.open(
            "a",
            encoding="utf-8",
        ) as file:
            # 카테고리 이름을 JSON 객체 한 줄로 저장합니다.
            file.write(
                json.dumps(
                    {"name": name},
                    ensure_ascii=False,
                )
                + "\n"
            )

        # 정상적으로 추가되면 True를 반환합니다.
        return True

    # 특정 카테고리를 삭제하는 메서드입니다.
    def remove(self, name: str) -> bool:
        # 카테고리 파일의 임시 파일 경로를 만듭니다.
        temp_path = self.paths.categories.with_suffix(
            ".jsonl.tmp"
        )

        # 삭제 대상 카테고리를 찾았는지 기록합니다.
        found = False

        try:
            # 임시 파일을 쓰기 모드로 엽니다.
            with temp_path.open(
                "w",
                encoding="utf-8",
            ) as output_file:
                # 기존 카테고리를 한 개씩 읽습니다.
                for category in self.iter_categories():
                    # 삭제 대상 카테고리라면 기록하지 않고 건너뜁니다.
                    if category == name:
                        found = True
                        continue

                    # 삭제 대상이 아닌 카테고리는 임시 파일에 기록합니다.
                    output_file.write(
                        json.dumps(
                            {"name": category},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

            # 카테고리를 찾았다면 임시 파일을 원본 파일로 교체합니다.
            if found:
                os.replace(
                    temp_path,
                    self.paths.categories,
                )

            else:
                # 해당 카테고리가 없었다면 원본 파일을 유지하고
                # 임시 파일만 삭제합니다.
                temp_path.unlink(missing_ok=True)

            # 삭제 성공 여부를 반환합니다.
            return found

        except Exception:
            # 오류 발생 시 임시 파일을 삭제합니다.
            temp_path.unlink(missing_ok=True)

            # 오류를 상위 코드로 다시 전달합니다.
            raise


# 월별 예산 데이터를 읽고 쓰는 저장소 클래스입니다.
class BudgetRepository:
    # DataPaths 객체를 받아 예산 파일 경로를 사용합니다.
    def __init__(self, paths: DataPaths) -> None:
        self.paths = paths

    # 예산 파일을 한 줄씩 읽어 Budget 객체를 반환하는 제너레이터입니다.
    def iter_budgets(self) -> Iterator[Budget]:
        # 예산 파일을 읽기 모드로 엽니다.
        with self.paths.budgets.open(
            "r",
            encoding="utf-8",
        ) as file:
            # 줄 번호와 줄 내용을 함께 읽습니다.
            for line_number, line in enumerate(file, start=1):
                # 빈 줄은 건너뜁니다.
                if not line.strip():
                    continue

                try:
                    # JSON 문자열을 딕셔너리로 변환합니다.
                    data = json.loads(line)

                    # 딕셔너리를 Budget 객체로 변환하여 한 건씩 반환합니다.
                    yield Budget.from_dict(data)

                except (
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                    ValueError,
                ) as exc:
                    # 예산 파일이 손상된 경우 줄 번호를 포함한 오류를 발생시킵니다.
                    raise ValueError(
                        "예산 저장 파일의 "
                        f"{line_number}번째 줄이 손상되었습니다."
                    ) from exc

    # 특정 월의 예산을 조회하는 메서드입니다.
    def get(self, month: str) -> Budget | None:
        # 저장된 예산을 한 건씩 확인합니다.
        for budget in self.iter_budgets():
            # 요청한 월과 같은 월의 예산을 찾으면 반환합니다.
            if budget.month == month:
                return budget

        # 해당 월의 예산이 없다면 None을 반환합니다.
        return None

    # 특정 월의 예산을 새로 저장하거나 기존 예산을 수정하는 메서드입니다.
    def set(self, new_budget: Budget) -> None:
        # 예산 파일의 임시 파일 경로를 만듭니다.
        temp_path = self.paths.budgets.with_suffix(
            ".jsonl.tmp"
        )

        # 같은 월의 기존 예산을 교체했는지 기록합니다.
        replaced_existing = False

        try:
            # 임시 파일을 쓰기 모드로 엽니다.
            with temp_path.open(
                "w",
                encoding="utf-8",
            ) as output_file:
                # 기존 예산 데이터를 한 건씩 읽습니다.
                for budget in self.iter_budgets():
                    # 기존 예산의 월과 새 예산의 월이 같다면,
                    # 기존 예산 대신 새 예산으로 교체합니다.
                    if budget.month == new_budget.month:
                        budget = new_budget
                        replaced_existing = True

                    # 현재 예산 정보를 임시 파일에 기록합니다.
                    output_file.write(
                        json.dumps(
                            budget.to_dict(),
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

                # 같은 월의 기존 예산이 없었다면,
                # 새 예산을 임시 파일 끝에 추가합니다.
                if not replaced_existing:
                    output_file.write(
                        json.dumps(
                            new_budget.to_dict(),
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

            # 임시 파일을 기존 예산 파일로 안전하게 교체합니다.
            os.replace(
                temp_path,
                self.paths.budgets,
            )

        except Exception:
            # 파일 처리 중 오류가 발생하면 임시 파일을 삭제합니다.
            temp_path.unlink(missing_ok=True)

            # 오류를 상위 코드로 다시 전달합니다.
            raise