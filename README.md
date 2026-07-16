# 파일 기반 가계부 콘솔 프로그램

## 1. 프로젝트 소개

이 프로젝트는 Python 표준 라이브러리만 사용하여 구현한 파일 기반 가계부 콘솔 프로그램입니다.

사용자는 터미널에서 명령어를 입력하여 다음 기능을 사용할 수 있습니다.

- 거래 추가
- 거래 목록 조회
- 조건 검색
- 월별 요약
- 예산 설정 및 조회
- 카테고리 관리
- 거래 수정
- 거래 삭제
- CSV 가져오기
- CSV 내보내기

거래 내역, 카테고리, 예산 정보는 데이터베이스가 아니라 JSONL 파일에 저장됩니다. 따라서 프로그램을 종료한 뒤 다시 실행해도 기존 데이터가 유지됩니다.

또한 다음 기술을 적용하여 단순한 스크립트가 아니라 유지보수 가능한 작은 서비스 형태로 구성했습니다.

- `dataclass` 기반 데이터 모델
- 제너레이터를 이용한 파일 스트리밍
- 데코레이터를 이용한 공통 예외 처리
- 타입 힌트
- CLI / Service / Repository / Model 계층 분리
- 임시 파일과 `os.replace()`를 이용한 안전한 수정 및 삭제
- CSV 행별 검증 및 오류 처리

보너스 과제는 구현하지 않았습니다.

---

## 2. 개발 환경

- Python 3.10 이상
- Python 표준 라이브러리만 사용
- 외부 라이브러리 설치 불필요
- 별도의 `pip install` 불필요

Python 버전 확인:

```bash
python --version
````

환경에 따라 다음 명령을 사용할 수도 있습니다.

```bash
python3 --version
```

---

## 3. 프로젝트 구조

```text
B2-1/
├── budget_app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── decorators.py
│   ├── formatters.py
│   ├── models.py
│   ├── repositories.py
│   ├── services.py
│   └── validators.py
├── tests/
│   └── import_mixed.csv
├── data/
│   ├── transactions.jsonl
│   ├── categories.jsonl
│   └── budgets.jsonl
├── .gitignore
└── README.md
```

`data/` 폴더와 내부 JSONL 파일은 프로그램을 처음 실행할 때 자동으로 생성됩니다.

---

## 4. 모듈이란?

Python에서 모듈은 관련된 함수, 클래스, 변수 등을 하나의 파일에 모아 둔 코드 단위입니다.

일반적으로 하나의 `.py` 파일을 하나의 모듈이라고 부릅니다.

예를 들어 다음 파일들은 각각 하나의 모듈입니다.

```text
models.py
validators.py
repositories.py
services.py
cli.py
```

다른 모듈에 있는 함수나 클래스를 `import`하여 재사용할 수 있습니다.

```python
from budget_app.models import Transaction
from budget_app.validators import validate_date
```

위 코드에서:

* `budget_app.models`는 `models.py` 모듈입니다.
* `Transaction`은 `models.py` 안에 정의된 클래스입니다.
* `budget_app.validators`는 `validators.py` 모듈입니다.
* `validate_date`는 `validators.py` 안에 정의된 함수입니다.

여러 모듈이 들어 있는 `budget_app/` 폴더 전체는 패키지라고 합니다.

```text
budget_app/          → 패키지
├── models.py        → 모듈
├── validators.py    → 모듈
├── services.py      → 모듈
└── repositories.py  → 모듈
```

파일과 모듈은 비슷하게 사용할 수 있지만 의미에는 약간 차이가 있습니다.

```text
models.py 파일
→ 컴퓨터에 실제로 저장된 파일을 의미

models.py 모듈
→ Python 코드 단위로서 import되어 사용되는 것을 의미
```

---

## 5. 각 모듈의 역할

### 5.1 `budget_app/__init__.py`

`budget_app` 폴더를 Python 패키지로 사용할 수 있게 하는 초기화 파일입니다.

현재 프로젝트에서는 별도의 초기화 작업이 필요하지 않으므로 파일을 비워 두었습니다.

이 파일이 있으면 패키지 내부의 모듈을 다음과 같이 불러올 수 있습니다.

```python
from budget_app.models import Transaction
from budget_app.services import TransactionService
```

---

### 5.2 `budget_app/__main__.py`

`python -m budget_app` 명령으로 프로그램을 실행할 때 사용되는 시작점 모듈입니다.

```python
from budget_app.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

`cli.py`에 있는 `main()` 함수를 실행하고, 반환값을 프로그램의 종료 코드로 사용합니다.

```text
0           → 정상 종료
0이 아닌 값 → 오류 종료
```

---

### 5.3 `budget_app/models.py`

거래 내역과 월별 예산의 데이터 구조를 정의하고, 객체와 JSONL 저장용 딕셔너리 사이의 변환을 담당하는 모델 모듈입니다.

주요 클래스는 다음과 같습니다.

```python
@dataclass
class Transaction:
    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] | None = None
```

`Transaction`은 거래 한 건을 표현합니다.

예시:

```python
Transaction(
    id="TX-000001",
    date="2026-07-17",
    type="expense",
    category="food",
    amount=15000,
    memo="lunch",
    tags=["meal"],
)
```

월별 예산은 `Budget` 클래스로 표현합니다.

```python
@dataclass
class Budget:
    month: str
    amount: int
```

객체를 JSONL에 저장하기 위해 딕셔너리로 변환합니다.

```python
transaction.to_dict()
```

JSONL에서 읽은 딕셔너리를 다시 객체로 변환할 수도 있습니다.

```python
Transaction.from_dict(data)
```

전체 변환 흐름은 다음과 같습니다.

```text
Transaction 객체
→ to_dict()
→ 딕셔너리
→ JSONL 저장

JSONL 데이터
→ 딕셔너리
→ from_dict()
→ Transaction 객체
```

---

### 5.4 `budget_app/validators.py`

사용자 입력값을 서비스 로직이나 파일 저장 단계로 넘기기 전에 날짜, 월, 금액, 거래 타입, 기간, 카테고리, 태그 형식을 검사하고 정리하는 검증 모듈입니다.

주요 함수는 다음과 같습니다.

| 함수                           | 역할                                |
| ---------------------------- | --------------------------------- |
| `validate_date()`            | 날짜가 `YYYY-MM-DD` 형식인지 검사          |
| `validate_month()`           | 월이 정확한 `YYYY-MM` 형식인지 검사          |
| `validate_amount()`          | 금액이 0보다 큰 양수인지 검사                 |
| `validate_type()`            | 거래 타입이 `income` 또는 `expense`인지 검사 |
| `validate_date_range()`      | 시작 날짜와 종료 날짜의 형식 및 순서를 검사         |
| `validate_positive_option()` | `--limit`, `--top` 등의 값이 양수인지 검사  |
| `normalize_category()`       | 카테고리의 공백을 제거하고 소문자로 변환            |
| `parse_tags()`               | 쉼표로 구분된 태그 문자열을 리스트로 변환           |

날짜 검증 예시:

```python
def validate_date(date_text: str) -> str:
    datetime.strptime(date_text, "%Y-%m-%d")
    return date_text
```

카테고리 이름은 다음과 같이 정리됩니다.

```text
"  Food  "
→ "food"
```

태그 문자열은 다음과 같이 변환됩니다.

```text
"meal, school, meal"
→ ["meal", "school"]
```

중복 태그는 한 번만 저장됩니다.

---

### 5.5 `budget_app/repositories.py`

JSONL 데이터 파일을 실제로 읽고 쓰는 저장소 모듈입니다.

다음 세 파일을 관리합니다.

```text
data/
├── transactions.jsonl
├── categories.jsonl
└── budgets.jsonl
```

주요 클래스는 다음과 같습니다.

| 클래스                     | 역할                       |
| ----------------------- | ------------------------ |
| `DataPaths`             | 데이터 폴더와 파일 경로 관리         |
| `TransactionRepository` | 거래 추가, 조회, ID 생성, 수정, 삭제 |
| `CategoryRepository`    | 카테고리 조회, 추가, 삭제          |
| `BudgetRepository`      | 월별 예산 조회 및 저장            |

#### 데이터 파일 자동 생성

프로그램을 처음 실행했을 때 파일이 없으면 자동으로 생성됩니다.

```python
paths.ensure_files()
```

카테고리 파일이 비어 있으면 다음 기본 카테고리가 자동으로 저장됩니다.

```text
food
transport
rent
salary
etc
```

#### 제너레이터 기반 파일 읽기

거래 파일은 `yield`를 사용하여 한 줄씩 읽습니다.

```python
def iter_transactions(self) -> Iterator[Transaction]:
    with self.paths.transactions.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            if line.strip():
                data = json.loads(line)
                yield Transaction.from_dict(data)
```

이 방식은 파일 전체를 한꺼번에 메모리에 올리지 않고 거래 한 건씩 처리할 수 있다는 장점이 있습니다.

#### 손상된 JSONL 데이터 처리

JSON 문법이 잘못되었거나 필수 값이 없는 줄이 있으면 줄 번호와 함께 오류를 발생시킵니다.

```text
거래 저장 파일의 3번째 줄이 손상되었습니다.
```

손상된 데이터를 조용히 무시하지 않고 사용자에게 문제 위치를 알려 줍니다.

#### 안전한 수정과 삭제

JSONL 파일 중간의 한 줄만 직접 수정하기 어렵기 때문에 수정과 삭제는 임시 파일을 사용합니다.

```text
기존 JSONL 파일을 한 줄씩 읽기
        ↓
수정되거나 삭제된 결과를 임시 파일에 쓰기
        ↓
모든 쓰기가 성공하면 os.replace() 실행
        ↓
임시 파일을 기존 파일로 교체
```

핵심 코드는 다음과 같습니다.

```python
os.replace(temp_path, self.paths.transactions)
```

원본 파일을 직접 덮어쓰는 것보다 데이터 손상 위험을 줄일 수 있습니다.

수정하거나 삭제할 ID가 존재하지 않으면 원본 파일을 교체하지 않고 임시 파일만 삭제합니다.

---

### 5.6 `budget_app/services.py`

프로그램의 실제 기능과 업무 규칙을 담당하는 서비스 모듈입니다.

Repository가 실제 파일을 읽고 쓰는 역할이라면, Service는 어떤 데이터를 허용하고 어떤 방식으로 처리할지 결정합니다.

주요 클래스는 다음과 같습니다.

| 클래스                  | 역할                       |
| -------------------- | ------------------------ |
| `CategoryService`    | 카테고리 추가, 조회, 삭제 규칙       |
| `TransactionService` | 거래 추가, 목록, 검색, 수정, 삭제    |
| `BudgetService`      | 월별 예산 설정 및 조회            |
| `SummaryService`     | 월별 수입, 지출, 잔액, 예산 사용률 계산 |
| `CsvService`         | CSV 가져오기와 내보내기           |

#### 거래 추가

거래를 추가하기 전에 날짜, 타입, 금액, 카테고리를 검증합니다.

```python
validate_date(date)
validate_type(transaction_type)
validate_amount(amount)
```

등록되지 않은 카테고리라면 저장하지 않습니다.

```python
if not self.category_repo.exists(normalized_category):
    raise ValueError(
        f"존재하지 않는 카테고리입니다: {normalized_category}"
    )
```

검증이 완료되면 새로운 거래 ID를 생성하고 JSONL 파일에 저장합니다.

---

#### 최신 거래 목록

`list --limit`은 `heapq.nlargest()`를 사용하여 최신 거래 일부만 선택합니다.

```python
return heapq.nlargest(
    limit,
    self.transaction_repo.iter_transactions(),
    key=self.latest_key,
)
```

전체 거래를 리스트로 만든 뒤 전부 정렬하는 방식보다 메모리 사용량을 줄일 수 있습니다.

정렬 기준은 다음과 같습니다.

```python
return transaction.date, transaction.id
```

먼저 날짜를 비교하고, 날짜가 같으면 거래 ID를 비교합니다.

---

#### 거래 검색

검색 조건은 다음과 같습니다.

* 시작 날짜
* 종료 날짜
* 카테고리
* 거래 타입
* 메모 키워드
* 태그

거래 파일을 한 건씩 확인한 뒤 조건을 만족하는 거래만 `yield`합니다.

```python
yield transaction
```

검색 조건 필터링은 제너레이터 기반으로 처리합니다.

다만 모든 검색 결과를 최신순으로 출력해야 하므로, 조건을 만족한 결과는 마지막에 정렬합니다.

```python
return sorted(
    matches,
    key=self.latest_key,
    reverse=True,
)
```

---

#### 거래 수정

수정할 항목이 하나도 입력되지 않으면 오류를 발생시킵니다.

```python
if all(value is None for value in values):
    raise ValueError(
        "수정할 항목을 하나 이상 입력해야 합니다."
    )
```

입력된 항목만 기존 거래에 반영합니다.

```python
if amount is not None:
    transaction.amount = amount
```

수정된 결과는 Repository의 임시 파일 교체 방식을 통해 안전하게 저장됩니다.

---

#### 거래 삭제

거래 삭제는 거래 ID를 기준으로 처리합니다.

```python
return self.transaction_repo.delete_by_id(
    transaction_id
)
```

ID가 존재하면 거래를 제외한 나머지 거래를 임시 파일에 저장한 뒤 원본 파일과 교체합니다.

---

#### 카테고리 삭제 규칙

거래에서 사용 중인 카테고리는 삭제할 수 없습니다.

```python
for transaction in self.transaction_repo.iter_transactions():
    if transaction.category == normalized:
        raise ValueError(
            "이미 거래에서 사용 중인 카테고리는 삭제할 수 없습니다."
        )
```

이 규칙은 거래에는 존재하지만 카테고리 목록에는 없는 데이터가 생기는 것을 막습니다.

---

#### 월별 요약

월별 요약에서는 다음 내용을 계산합니다.

* 총수입
* 총지출
* 잔액
* 카테고리별 지출 합계
* 카테고리별 지출 TOP N
* 예산 사용률
* 예산 초과 여부

예산 사용률 계산:

```python
usage_rate = total_expense / budget.amount * 100
```

잔액 계산:

```python
balance = total_income - total_expense
```

카테고리별 지출은 `defaultdict(int)`를 사용해 누적합니다.

```python
category_expenses[transaction.category] += transaction.amount
```

---

#### CSV 가져오기

CSV의 필수 열은 다음과 같습니다.

```text
date
type
category
amount
```

선택 열은 다음과 같습니다.

```text
memo
tags
```

CSV 헤더가 없거나 필수 열이 빠져 있으면 전체 import를 중단합니다.

각 데이터 행은 한 줄씩 처리합니다.

정상 행은 저장하고:

```python
imported += 1
```

잘못된 행은 건너뜁니다.

```python
skipped += 1
errors.append(f"{row_number}행: {exc}")
```

따라서 잘못된 행이 하나 있어도 이후의 정상 행은 계속 처리됩니다.

---

### 5.7 `budget_app/formatters.py`

거래 데이터를 콘솔에서 보기 좋은 문자열로 변환하고 출력하는 모듈입니다.

거래 한 건은 다음과 같은 형식으로 변환됩니다.

```python
def format_transaction(transaction: Transaction) -> str:
    return (
        f"{transaction.id} | "
        f"{transaction.date} | "
        f"{transaction.type:<7} | "
        f"{transaction.category:<12} | "
        f"{transaction.amount:>10} | "
        f"{transaction.memo}"
    )
```

예시 출력:

```text
TX-000001 | 2026-07-17 | expense | food         |      15000 | lunch | meal
```

`print_transactions()`는 리스트뿐 아니라 제너레이터 등 반복 가능한 값을 받을 수 있습니다.

```python
def print_transactions(
    transactions: Iterable[Transaction],
) -> None:
```

출력할 거래가 없으면 다음 안내 메시지를 출력합니다.

```text
[안내] 조건에 맞는 거래 내역이 없습니다.
```

---

### 5.8 `budget_app/decorators.py`

CLI 실행 중 반복되는 공통 예외 처리를 분리한 데코레이터 모듈입니다.

다음과 같이 `main()` 함수에 적용합니다.

```python
@handle_cli_errors
def main() -> int:
    ...
```

처리하는 주요 오류는 다음과 같습니다.

| 오류                  | 상황                | 종료 코드 |
| ------------------- | ----------------- | ----: |
| `FileNotFoundError` | 입력한 파일을 찾을 수 없음   |     2 |
| `PermissionError`   | 파일 접근 권한 없음       |     3 |
| `ValueError`        | 날짜, 금액, 옵션 등이 잘못됨 |     4 |
| `OSError`           | 기타 파일 처리 오류       |     5 |
| `KeyboardInterrupt` | 사용자가 `Ctrl+C`로 종료 |   130 |

오류가 발생하면 Python 스택트레이스를 그대로 출력하지 않고 원인과 해결 힌트를 출력합니다.

```text
[오류] 날짜 형식이 올바르지 않습니다.
[힌트] 입력값과 명령어 옵션을 다시 확인하세요.
```

데코레이터를 사용했기 때문에 각 명령어마다 같은 `try-except` 코드를 반복해서 작성하지 않아도 됩니다.

---

### 5.9 `budget_app/cli.py`

사용자가 입력한 명령어와 옵션을 해석하고 적절한 서비스 기능을 호출하는 CLI 모듈입니다.

`argparse`를 사용하여 다음 명령어를 정의합니다.

```text
add
list
search
summary
budget
category
update
delete
import
export
```

예를 들어 다음 명령을 실행하면:

```bash
python -m budget_app list --limit 5
```

`argparse`가 다음 값을 분석합니다.

```text
command = "list"
limit = 5
```

그 후 `TransactionService`의 목록 기능을 호출합니다.

```python
transactions = transaction_service.list_latest(args.limit)
print_transactions(transactions)
```

`cli.py`는 직접 JSONL 파일을 수정하지 않습니다.

```text
CLI
→ 사용자 입력과 출력

Service
→ 기능과 업무 규칙

Repository
→ 실제 파일 읽기와 쓰기
```

---

### 5.10 파일별 역할 요약

| 파일                | 구분         | 주요 역할                             |
| ----------------- | ---------- | --------------------------------- |
| `__init__.py`     | 패키지 초기화 파일 | `budget_app`을 Python 패키지로 사용      |
| `__main__.py`     | 실행 진입점 모듈  | `python -m budget_app` 실행 처리      |
| `models.py`       | 모델 모듈      | `Transaction`, `Budget` 데이터 구조 정의 |
| `validators.py`   | 검증 모듈      | 날짜, 금액, 타입, 기간, 카테고리, 태그 검증       |
| `repositories.py` | 저장소 모듈     | JSONL 파일 읽기, 쓰기, 수정, 삭제           |
| `services.py`     | 서비스 모듈     | 거래, 예산, 요약, CSV 업무 로직             |
| `formatters.py`   | 출력 모듈      | 거래 데이터를 보기 좋은 문자열로 변환             |
| `decorators.py`   | 공통 처리 모듈   | 오류 메시지와 종료 코드 처리                  |
| `cli.py`          | CLI 모듈     | 명령어 분석, 사용자 입력 및 결과 출력            |

---

## 6. 전체 실행 흐름

프로그램의 주요 실행 흐름은 다음과 같습니다.

```text
사용자 명령어 입력
        ↓
__main__.py
        ↓
cli.py
        ↓
services.py
        ↓
repositories.py
        ↓
JSONL 데이터 파일
```

예를 들어 사용자가 거래를 추가하면 다음 순서로 처리됩니다.

```text
python -m budget_app add
        ↓
cli.py에서 날짜, 타입, 카테고리, 금액 등을 입력
        ↓
TransactionService가 입력값 검증
        ↓
Transaction 객체 생성
        ↓
TransactionRepository가 transactions.jsonl에 저장
```

---

## 7. 실행 방법

프로젝트 루트 폴더에서 실행합니다.

```bash
python -m budget_app <command> [options]
```

환경에 따라 다음과 같이 실행할 수도 있습니다.

```bash
python3 -m budget_app <command> [options]
```

전체 도움말:

```bash
python -m budget_app --help
```

각 명령어별 도움말:

```bash
python -m budget_app add --help
python -m budget_app list --help
python -m budget_app search --help
python -m budget_app summary --help
python -m budget_app budget --help
python -m budget_app category --help
python -m budget_app update --help
python -m budget_app delete --help
python -m budget_app import --help
python -m budget_app export --help
```

---

## 8. 데이터 저장 폴더 변경

기본 데이터 폴더는 `data/`입니다.

```bash
python -m budget_app category list
```

다른 데이터 폴더를 사용하려면 `--data-dir` 옵션을 명령어 앞에 입력합니다.

```bash
python -m budget_app --data-dir test_data category list
```

```bash
python -m budget_app --data-dir test_data add
```

```bash
python -m budget_app --data-dir test_data list --limit 5
```

`--data-dir`은 최상위 옵션이므로 하위 명령어보다 앞에 작성합니다.

올바른 예:

```bash
python -m budget_app --data-dir test_data list --limit 5
```

권장하지 않는 예:

```bash
python -m budget_app list --data-dir test_data --limit 5
```

---

## 9. 데이터 저장 방식

내부 저장 형식은 JSONL입니다.

JSONL은 한 줄에 하나의 JSON 객체를 저장하는 형식입니다.

### 9.1 거래 파일

`data/transactions.jsonl`

```json
{"id":"TX-000001","date":"2026-07-17","type":"expense","category":"food","amount":15000,"memo":"lunch","tags":["meal"]}
{"id":"TX-000002","date":"2026-07-18","type":"income","category":"salary","amount":3000000,"memo":"monthly salary","tags":["work"]}
```

### 9.2 카테고리 파일

`data/categories.jsonl`

```json
{"name":"food"}
{"name":"transport"}
{"name":"rent"}
{"name":"salary"}
{"name":"etc"}
```

### 9.3 예산 파일

`data/budgets.jsonl`

```json
{"month":"2026-07","amount":500000}
```

---

## 10. 주요 명령어

### 10.1 거래 추가: `add`

거래를 대화형으로 추가합니다.

```bash
python -m budget_app add
```

입력 예시:

```text
날짜(YYYY-MM-DD): 2026-07-17
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): lunch
태그(쉼표로 구분, 없으면 엔터): meal,school
```

성공 예시:

```text
[저장 완료] id=TX-000001
```

등록된 카테고리만 사용할 수 있습니다.

---

### 10.2 거래 목록: `list`

최신순으로 거래를 출력합니다.

```bash
python -m budget_app list
```

출력 개수 지정:

```bash
python -m budget_app list --limit 5
```

예시 출력:

```text
TX-000003 | 2026-07-19 | expense | transport    |       2500 | bus | commute
TX-000002 | 2026-07-18 | income  | salary       |    3000000 | monthly salary | work
TX-000001 | 2026-07-17 | expense | food         |      15000 | lunch | meal
```

`--limit`은 0보다 큰 정수여야 합니다.

---

### 10.3 거래 검색: `search`

조건에 맞는 거래를 검색합니다.

사용 가능한 옵션:

| 옵션           | 설명                    |
| ------------ | --------------------- |
| `--from`     | 검색 시작 날짜              |
| `--to`       | 검색 종료 날짜              |
| `--category` | 카테고리                  |
| `--type`     | `income` 또는 `expense` |
| `--q`        | 메모 검색어                |
| `--tag`      | 태그 검색어                |

카테고리 검색:

```bash
python -m budget_app search --category food
```

타입 검색:

```bash
python -m budget_app search --type expense
```

기간 검색:

```bash
python -m budget_app search --from 2026-07-01 --to 2026-07-31
```

메모 검색:

```bash
python -m budget_app search --q lunch
```

태그 검색:

```bash
python -m budget_app search --tag meal
```

여러 조건을 함께 사용할 수도 있습니다.

```bash
python -m budget_app search --type expense --category food --from 2026-07-01 --to 2026-07-31
```

시작 날짜가 종료 날짜보다 늦으면 오류가 발생합니다.

---

### 10.4 월별 요약: `summary`

특정 월의 총수입, 총지출, 잔액, 카테고리별 지출 TOP N을 출력합니다.

```bash
python -m budget_app summary --month 2026-07 --top 3
```

예시 출력:

```text
총 수입: 3000000원
총 지출: 17500원
잔액: 2982500원
예산: 500000원 (사용률 3.5%)

지출 TOP 3
1) food 15000원
2) transport 2500원
```

예산을 초과하면 다음 경고를 출력합니다.

```text
[경고] 월 예산을 초과했습니다.
```

`--top`은 0보다 큰 정수여야 합니다.

---

### 10.5 예산 설정: `budget set`

월별 예산을 설정하거나 수정합니다.

```bash
python -m budget_app budget set --month 2026-07 --amount 500000
```

성공 예시:

```text
[저장 완료] 2026-07 예산 500000원
```

같은 월에 다시 설정하면 기존 예산이 새 금액으로 교체됩니다.

---

### 10.6 예산 조회: `budget get`

저장된 월별 예산을 조회합니다.

```bash
python -m budget_app budget get --month 2026-07
```

예산이 있는 경우:

```text
2026-07 예산: 500000원
```

예산이 없는 경우:

```text
[안내] 2026-07에 설정된 예산이 없습니다.
```

---

### 10.7 카테고리 추가: `category add`

카테고리를 대화형으로 추가합니다.

```bash
python -m budget_app category add
```

입력 예시:

```text
카테고리명: coffee
```

성공 예시:

```text
[저장 완료] category=coffee
```

카테고리는 앞뒤 공백이 제거되고 소문자로 저장됩니다.

```text
" Coffee "
→ "coffee"
```

이미 존재하는 카테고리는 중복 추가되지 않습니다.

---

### 10.8 카테고리 목록: `category list`

전체 카테고리를 출력합니다.

```bash
python -m budget_app category list
```

예시:

```text
- etc
- food
- rent
- salary
- transport
```

목록은 정렬되어 출력됩니다.

---

### 10.9 카테고리 삭제: `category remove`

카테고리를 삭제합니다.

```bash
python -m budget_app category remove --name coffee
```

성공 예시:

```text
[삭제 완료] category=coffee
```

거래에서 사용 중인 카테고리는 삭제할 수 없습니다.

```text
[오류] 이미 거래에서 사용 중인 카테고리는 삭제할 수 없습니다.
```

---

### 10.10 거래 수정: `update`

이 프로젝트는 옵션 기반 수정 방식을 사용합니다.

기본 형식:

```bash
python -m budget_app update --id <거래 ID> [수정 옵션]
```

사용 가능한 수정 옵션:

```text
--date
--type
--category
--amount
--memo
--tags
```

금액과 메모 수정:

```bash
python -m budget_app update --id TX-000001 --amount 20000 --memo "dinner"
```

카테고리 수정:

```bash
python -m budget_app update --id TX-000001 --category transport
```

태그 수정:

```bash
python -m budget_app update --id TX-000001 --tags "daily,commute"
```

메모를 빈 값으로 변경:

```bash
python -m budget_app update --id TX-000001 --memo ""
```

수정할 필드를 하나도 입력하지 않으면 오류가 발생합니다.

```bash
python -m budget_app update --id TX-000001
```

오류 예시:

```text
[오류] 수정할 항목을 하나 이상 입력해야 합니다.
```

존재하지 않는 ID:

```text
[안내] 해당 ID의 거래가 없습니다: TX-999999
```

---

### 10.11 거래 삭제: `delete`

거래 ID를 기준으로 삭제합니다.

```bash
python -m budget_app delete --id TX-000001
```

성공 예시:

```text
[삭제 완료] id=TX-000001
```

존재하지 않는 ID:

```text
[안내] 해당 ID의 거래가 없습니다: TX-999999
```

---

### 10.12 CSV 가져오기: `import`

CSV 파일의 거래를 일괄 등록합니다.

```bash
python -m budget_app import --from tests/import_mixed.csv
```

Windows PowerShell에서는 다음처럼 작성할 수도 있습니다.

```powershell
python -m budget_app import --from tests\import_mixed.csv
```

각 행은 독립적으로 처리됩니다.

정상 행은 저장하고, 잘못된 행은 건너뜁니다.

예시:

```text
[건너뜀] 4행: 날짜 형식이 올바르지 않습니다. 예: 2026-07-17
[건너뜀] 5행: 거래 타입은 income 또는 expense만 가능합니다.
[완료] imported=3, skipped=2
```

---

### 10.13 CSV 내보내기: `export`

특정 월의 거래를 내보냅니다.

```bash
python -m budget_app export --out export.csv --month 2026-07
```

기간을 기준으로 내보냅니다.

```bash
python -m budget_app export --out export.csv --from 2026-07-01 --to 2026-07-31
```

성공 예시:

```text
[완료] export.csv (5 records)
```

`export`는 다음 조건 중 하나 이상을 반드시 받아야 합니다.

```text
--month
--from
--to
```

조건 없이 실행하면 오류가 발생합니다.

```bash
python -m budget_app export --out export.csv
```

---

## 11. Import / Export CSV 스키마

CSV 파일은 UTF-8 인코딩과 헤더를 사용합니다.

| column     | required | 설명                    |
| ---------- | -------- | --------------------- |
| `date`     | Y        | `YYYY-MM-DD` 형식       |
| `type`     | Y        | `income` 또는 `expense` |
| `category` | Y        | 등록된 카테고리              |
| `amount`   | Y        | 0보다 큰 정수              |
| `memo`     | N        | 메모 문자열                |
| `tags`     | N        | 쉼표로 구분된 태그 문자열        |

CSV 예시:

```csv
date,type,category,amount,memo,tags
2026-07-20,expense,food,12000,coffee,drink
2026-07-21,expense,transport,2500,bus,commute
2026-07-25,income,salary,100000,part time,work
```

Import는 일반 UTF-8과 BOM이 포함된 UTF-8 파일을 모두 읽을 수 있도록 `utf-8-sig` 인코딩을 사용합니다.

---

## 12. 혼합 CSV 테스트 파일

`tests/import_mixed.csv`는 정상 행과 오류 행이 섞인 import 테스트용 파일입니다.

```csv
date,type,category,amount,memo,tags
2026-07-20,expense,food,12000,coffee,drink
2026-07-21,expense,transport,2500,bus,commute
2026-13-40,expense,food,10000,bad date,error
2026-07-22,wrong,food,5000,bad type,error
2026-07-23,expense,unknown,6000,bad category,error
2026-07-24,expense,food,-100,bad amount,error
2026-07-25,income,salary,100000,part time,work
```

실행:

```bash
python -m budget_app --data-dir test_data import --from tests/import_mixed.csv
```

예상 결과:

```text
imported=3
skipped=4
```

이 파일은 영구 저장 파일이 아니라 import 기능을 검증하기 위한 테스트 입력 파일입니다.

---

## 13. 오류 처리와 종료 코드

오류가 발생하면 스택트레이스 대신 원인과 해결 힌트를 출력합니다.

날짜 오류 예시:

```text
[오류] 날짜 형식이 올바르지 않습니다. 예: 2026-07-17
[힌트] 입력값과 명령어 옵션을 다시 확인하세요.
```

파일 경로 오류 예시:

```text
[오류] 파일을 찾을 수 없습니다: missing.csv
[힌트] 입력한 파일 경로를 확인하세요.
```

종료 코드:

| 종료 코드 | 의미                       |
| ----: | ------------------------ |
|   `0` | 정상 종료                    |
|   `2` | 파일을 찾을 수 없음 또는 CLI 사용 오류 |
|   `3` | 파일 접근 권한 오류              |
|   `4` | 입력값 검증 오류                |
|   `5` | 기타 파일 처리 오류              |
| `130` | 사용자가 `Ctrl+C`로 중단        |

PowerShell에서 최근 종료 코드 확인:

```powershell
$LASTEXITCODE
```

macOS 또는 Linux:

```bash
echo $?
```

---

## 14. 주요 기술 구현

### 14.1 Dataclass

거래와 예산 데이터 구조를 명확하게 정의하기 위해 `dataclass`를 사용했습니다.

```python
@dataclass
class Transaction:
    id: str
    date: str
    type: str
    category: str
    amount: int
```

반복적인 생성자 코드를 줄이고 데이터 구조를 쉽게 확인할 수 있습니다.

---

### 14.2 타입 힌트

함수의 입력값과 반환값을 명확하게 표현하기 위해 타입 힌트를 사용했습니다.

```python
def validate_amount(amount: int) -> int:
```

```python
def iter_transactions(self) -> Iterator[Transaction]:
```

```python
def get_budget(self, month: str) -> Budget | None:
```

타입 힌트는 코드의 계약을 명확하게 보여 주고 코드 이해와 유지보수에 도움을 줍니다.

---

### 14.3 제너레이터

JSONL 파일을 한 줄씩 읽기 위해 `yield` 기반 제너레이터를 사용합니다.

```python
yield Transaction.from_dict(data)
```

파일 전체를 즉시 리스트로 변환하지 않고 필요한 데이터를 순차적으로 처리할 수 있습니다.

`list --limit`에서는 `heapq.nlargest()`를 사용해 필요한 최신 거래만 유지합니다.

검색에서는 파일을 한 건씩 필터링하고, 일치한 결과만 최신순 정렬합니다.

---

### 14.4 데코레이터

공통 예외 처리를 `handle_cli_errors` 데코레이터로 분리했습니다.

```python
@handle_cli_errors
def main() -> int:
    ...
```

각 명령어마다 같은 `try-except` 코드를 반복하지 않아도 되며, 오류 메시지와 종료 코드를 일관되게 유지할 수 있습니다.

---

### 14.5 JSONL 저장

내부 데이터 저장 형식으로 JSONL을 선택했습니다.

장점:

* 한 줄에 한 객체 저장
* 제너레이터 기반 순차 읽기 가능
* 태그 리스트를 자연스럽게 저장 가능
* 새 거래를 파일 끝에 쉽게 추가 가능

단점:

* 파일 중간의 한 줄만 직접 수정하기 어려움
* 수정과 삭제 시 파일 재작성이 필요함
* Excel에서 직접 보기에는 CSV보다 불편함

따라서 내부 저장에는 JSONL을 사용하고, 외부 교환에는 CSV를 사용했습니다.

---

### 14.6 임시 파일과 원자적 교체

수정과 삭제 시 원본 JSONL 파일을 직접 수정하지 않습니다.

```text
원본 파일 읽기
→ 임시 파일 작성
→ 작성 완료
→ os.replace()로 교체
```

```python
os.replace(temp_path, self.paths.transactions)
```

파일 쓰기 도중 오류가 발생하면 임시 파일을 제거하고 원본 파일은 유지합니다.

---

### 14.7 계층 분리

프로그램은 역할에 따라 여러 계층으로 분리되어 있습니다.

```text
Model
→ 데이터 구조

Validator
→ 입력 검증

Repository
→ 파일 읽기와 쓰기

Service
→ 업무 규칙과 계산

CLI
→ 사용자 입력과 출력
```

이 구조를 사용하면 특정 기능을 수정할 때 관련 모듈만 변경할 수 있습니다.

예를 들어 날짜 검증 규칙을 변경하려면 `validators.py`를 중심으로 수정하면 됩니다.

---

## 15. 기능 체크리스트

| 기능                            | 구현 여부 |
| ----------------------------- | ----- |
| 거래 추가 `add`                   | 완료    |
| 거래 목록 `list --limit`          | 완료    |
| 거래 검색 `search`                | 완료    |
| 월별 요약 `summary --month --top` | 완료    |
| 예산 설정 `budget set`            | 완료    |
| 예산 조회 `budget get`            | 완료    |
| 예산 사용률 출력                     | 완료    |
| 예산 초과 경고                      | 완료    |
| 카테고리 추가 `category add`        | 완료    |
| 카테고리 목록 `category list`       | 완료    |
| 카테고리 삭제 `category remove`     | 완료    |
| 사용 중인 카테고리 삭제 방지              | 완료    |
| 거래 수정 `update --id`           | 완료    |
| 수정 필드 미입력 오류 처리               | 완료    |
| 거래 삭제 `delete --id`           | 완료    |
| CSV 가져오기 `import --from`      | 완료    |
| CSV 내보내기 `export --out`       | 완료    |
| CSV 필수 헤더 검증                  | 완료    |
| CSV 오류 행 개별 건너뛰기              | 완료    |
| CSV 오류 행 번호 출력                | 완료    |
| 세 개 이상 데이터 파일 저장              | 완료    |

---

## 16. 기술 요구사항 체크리스트

| 요구사항                   | 적용 여부 |
| ---------------------- | ----- |
| Python 3.10 이상         | 적용    |
| 표준 라이브러리만 사용           | 적용    |
| 외부 패키지 미사용             | 적용    |
| 최소 3개 이상 모듈            | 적용    |
| 최소 2개 이상 클래스           | 적용    |
| `dataclass` 사용         | 적용    |
| 타입 힌트 사용               | 적용    |
| `yield` 제너레이터 사용       | 적용    |
| 데코레이터 사용               | 적용    |
| 거래/카테고리/예산 파일 분리       | 적용    |
| 기본 카테고리 자동 생성          | 적용    |
| `--data-dir` 지원        | 적용    |
| update/delete 임시 파일 사용 | 적용    |
| `os.replace()` 사용      | 적용    |
| 오류 시 스택트레이스 미출력        | 적용    |
| 오류 시 0이 아닌 종료 코드       | 적용    |
| README 실행 방법 작성        | 적용    |
| 저장 파일 위치 및 형식 설명       | 적용    |
| 명령어 사용 예시 포함           | 적용    |
| CSV 스키마 설명             | 적용    |

---

## 17. 전체 기능 테스트 순서

테스트 데이터가 기존 데이터와 섞이지 않도록 `test_data/` 폴더를 사용하는 것을 권장합니다.

### 17.1 문법 검사

```bash
python -m compileall budget_app
```

### 17.2 전체 도움말

```bash
python -m budget_app --help
```

### 17.3 테스트 데이터 폴더 생성

```bash
python -m budget_app --data-dir test_data category list
```

### 17.4 카테고리 추가

```bash
python -m budget_app --data-dir test_data category add
```

### 17.5 거래 추가

```bash
python -m budget_app --data-dir test_data add
```

### 17.6 거래 목록

```bash
python -m budget_app --data-dir test_data list --limit 10
```

### 17.7 검색

```bash
python -m budget_app --data-dir test_data search --type expense
```

```bash
python -m budget_app --data-dir test_data search --category food
```

```bash
python -m budget_app --data-dir test_data search --from 2026-07-01 --to 2026-07-31
```

### 17.8 예산 설정

```bash
python -m budget_app --data-dir test_data budget set --month 2026-07 --amount 500000
```

### 17.9 예산 조회

```bash
python -m budget_app --data-dir test_data budget get --month 2026-07
```

### 17.10 월별 요약

```bash
python -m budget_app --data-dir test_data summary --month 2026-07 --top 3
```

### 17.11 거래 수정

```bash
python -m budget_app --data-dir test_data update --id TX-000001 --amount 20000 --memo "dinner"
```

### 17.12 존재하지 않는 ID 수정

```bash
python -m budget_app --data-dir test_data update --id TX-999999 --amount 10000
```

### 17.13 거래 삭제

```bash
python -m budget_app --data-dir test_data delete --id TX-000001
```

### 17.14 혼합 CSV 가져오기

```bash
python -m budget_app --data-dir test_data import --from tests/import_mixed.csv
```

### 17.15 CSV 내보내기

```bash
python -m budget_app --data-dir test_data export --out tests/export_july.csv --month 2026-07
```

### 17.16 데이터 파일 확인

Windows PowerShell:

```powershell
Get-ChildItem test_data
```

macOS/Linux:

```bash
ls test_data
```

예상 파일:

```text
transactions.jsonl
categories.jsonl
budgets.jsonl
```

---

## 18. 입력 오류 테스트 예시

잘못된 날짜:

```text
2026-13-40
```

0원:

```text
0
```

음수 금액:

```text
-1000
```

잘못된 기간:

```bash
python -m budget_app search --from 2026-07-31 --to 2026-07-01
```

잘못된 limit:

```bash
python -m budget_app list --limit 0
```

잘못된 top:

```bash
python -m budget_app summary --month 2026-07 --top 0
```

수정 필드 없음:

```bash
python -m budget_app update --id TX-000001
```

내보내기 조건 없음:

```bash
python -m budget_app export --out export.csv
```

---

## 19. 모듈 분리의 장점

### 책임이 명확함

각 모듈이 서로 다른 역할을 담당합니다.

```text
cli.py
→ 사용자 입력과 출력

services.py
→ 업무 규칙

repositories.py
→ 파일 저장

validators.py
→ 입력 검증

models.py
→ 데이터 구조
```

### 수정이 쉬움

날짜 검증 규칙을 변경할 경우 `validators.py`를 중심으로 수정하면 됩니다.

### 중복 코드 감소

`add`와 `import`가 동일한 `add_transaction()` 기능을 재사용합니다.

### 테스트가 쉬움

CLI 전체를 실행하지 않고도 Validator, Service, Repository를 각각 확인할 수 있습니다.

### 저장 방식 변경이 쉬움

향후 JSONL 대신 데이터베이스를 사용하더라도 Repository 계층을 중심으로 변경할 수 있습니다.

---

## 20. 마무리

이 프로젝트는 단순히 수입과 지출을 저장하는 프로그램이 아니라 파일 기반 저장소를 사용하는 작은 콘솔 서비스입니다.

거래, 카테고리, 예산 데이터를 세 개의 JSONL 파일로 분리하여 영구 저장하며, 제너레이터를 통해 파일을 순차적으로 읽습니다.

또한 데코레이터를 통해 공통 예외 처리를 분리하고, 타입 힌트와 `dataclass`를 사용하여 데이터 구조와 함수의 계약을 명확히 했습니다.

수정 및 삭제에서는 임시 파일과 `os.replace()`를 사용하여 원본 데이터 손상 위험을 줄였습니다.

CSV import에서는 정상 행과 오류 행을 각각 처리하여 하나의 잘못된 행 때문에 전체 작업이 중단되지 않도록 구성했습니다.
