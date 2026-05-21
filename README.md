# 파일 기반 가계부 콘솔 프로그램

## 1. 프로젝트 개요

이 프로젝트는 Python 표준 라이브러리만 사용하여 구현한 파일 기반 가계부 콘솔 프로그램입니다.

사용자는 터미널에서 명령어를 입력하여 수입과 지출 내역을 추가하고, 목록 조회, 조건 검색, 월별 요약, 예산 설정, 카테고리 관리, 거래 수정/삭제, CSV 가져오기/내보내기 기능을 사용할 수 있습니다.

이 프로그램은 데이터베이스를 사용하지 않고 파일 기반으로 데이터를 저장합니다. 따라서 프로그램을 종료한 뒤에도 거래 내역, 카테고리, 예산 정보가 `data/` 폴더 안의 파일에 영구 저장됩니다.

또한 단순한 기능 구현에 그치지 않고, 제너레이터 기반 스트리밍 처리, 데코레이터를 활용한 공통 예외 처리, 타입 힌트, 모듈 분리 구조를 적용하여 유지보수 가능한 작은 서비스 형태로 설계했습니다.

---

## 2. 개발 환경 및 실행 조건

- Python 3.10 이상
- 표준 라이브러리만 사용
- 별도의 외부 패키지 설치 없음
- `pip install` 필요 없음

Python 버전 확인:

```bash
python3 --version
```

또는 환경에 따라:

```bash
python --version
```

---

## 3. 프로젝트 구조

```text
budget_app_project/
├── budget_app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── models.py
│   ├── repositories.py
│   ├── services.py
│   ├── validators.py
│   ├── decorators.py
│   └── formatters.py
├── data/
│   ├── transactions.jsonl
│   ├── categories.jsonl
│   └── budgets.jsonl
└── README.md
```

각 모듈의 역할은 다음과 같습니다.

| 파일 | 역할 |
| --- | --- |
| `__main__.py` | `python -m budget_app` 실행 진입점 |
| `cli.py` | argparse 기반 명령어 처리 |
| `models.py` | Transaction, Budget 등 데이터 모델 정의 |
| `repositories.py` | JSONL 파일 읽기/쓰기, 저장소 처리 |
| `services.py` | 거래, 카테고리, 예산, 요약, CSV 처리 로직 |
| `validators.py` | 날짜, 금액, 타입 등 입력값 검증 |
| `decorators.py` | CLI 예외 처리 데코레이터 |
| `formatters.py` | 거래 내역 출력 형식 처리 |

---

## 4. 실행 방법

프로젝트 루트 폴더에서 다음 형식으로 실행합니다.

```bash
python3 -m budget_app <command> [options]
```

예시:

```bash
python3 -m budget_app --help
```

환경에 따라 `python3` 대신 `python`을 사용할 수 있습니다.

```bash
python -m budget_app --help
```

---

## 5. 전체 명령어 목록

이 프로그램은 다음 명령어를 제공합니다.

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

전체 도움말 확인:

```bash
python3 -m budget_app --help
```

각 명령어별 도움말 확인:

```bash
python3 -m budget_app add --help
python3 -m budget_app list --help
python3 -m budget_app search --help
python3 -m budget_app summary --help
python3 -m budget_app budget --help
python3 -m budget_app category --help
python3 -m budget_app update --help
python3 -m budget_app delete --help
python3 -m budget_app import --help
python3 -m budget_app export --help
```

---

## 6. 데이터 저장 방식

이 프로젝트는 내부 저장 방식으로 JSONL 형식을 사용합니다.

JSONL은 한 줄에 하나의 JSON 객체를 저장하는 방식입니다. 파일 전체를 한 번에 읽지 않고 한 줄씩 읽을 수 있기 때문에 제너레이터 기반 스트리밍 처리에 적합합니다.

데이터는 기본적으로 `data/` 폴더에 저장됩니다.

```text
data/
├── transactions.jsonl
├── categories.jsonl
└── budgets.jsonl
```

각 파일의 역할은 다음과 같습니다.

| 파일 | 설명 |
| --- | --- |
| `transactions.jsonl` | 수입/지출 거래 내역 저장 |
| `categories.jsonl` | 카테고리 목록 저장 |
| `budgets.jsonl` | 월별 예산 정보 저장 |

프로그램을 처음 실행할 때 파일이 없으면 자동으로 생성됩니다.

---

## 7. 저장 데이터 예시

### 거래 내역 예시

`transactions.jsonl`

```json
{"id":"TX-000001","date":"2024-01-15","type":"expense","category":"food","amount":15000,"memo":"lunch","tags":["meal"]}
{"id":"TX-000002","date":"2024-01-16","type":"income","category":"salary","amount":3000000,"memo":"monthly salary","tags":["work"]}
```

### 카테고리 예시

`categories.jsonl`

```json
{"name":"food"}
{"name":"transport"}
{"name":"rent"}
{"name":"salary"}
{"name":"etc"}
```

### 예산 예시

`budgets.jsonl`

```json
{"month":"2024-01","amount":500000}
```

---

## 8. 주요 기능 사용 방법

## 8.1 거래 추가: `add`

거래를 대화형 입력 방식으로 추가합니다.

```bash
python3 -m budget_app add
```

실행 후 다음 정보를 순서대로 입력합니다.

```text
날짜(YYYY-MM-DD)
타입(income/expense)
카테고리
금액(양수)
메모
태그
```

예시:

```text
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): lunch
태그(쉼표로 구분, 없으면 엔터): meal
```

성공 시 생성된 거래 ID가 출력됩니다.

```text
[저장 완료] id=TX-000001
```

---

## 8.2 거래 목록 조회: `list`

최신순으로 거래 내역을 출력합니다.

```bash
python3 -m budget_app list --limit 5
```

`--limit` 옵션으로 출력할 거래 개수를 지정할 수 있습니다.

예시 출력:

```text
TX-000002 | 2024-01-16 | income  | salary     | 3000000 | monthly salary | work
TX-000001 | 2024-01-15 | expense | food       | 15000 | lunch | meal
```

---

## 8.3 거래 검색: `search`

조건에 맞는 거래 내역을 검색합니다.

사용 가능한 검색 조건은 다음과 같습니다.

| 옵션 | 설명 |
| --- | --- |
| `--from` | 시작 날짜 |
| `--to` | 종료 날짜 |
| `--category` | 카테고리 |
| `--type` | income 또는 expense |
| `--q` | 메모 키워드 |
| `--tag` | 태그 |

예시:

```bash
python3 -m budget_app search --category food
```

```bash
python3 -m budget_app search --type expense
```

```bash
python3 -m budget_app search --from 2024-01-01 --to 2024-01-31
```

```bash
python3 -m budget_app search --q lunch
```

```bash
python3 -m budget_app search --tag meal
```

---

## 8.4 월별 요약: `summary`

특정 월의 총수입, 총지출, 잔액, 카테고리별 지출 TOP N을 출력합니다.

```bash
python3 -m budget_app summary --month 2024-01 --top 3
```

예시 출력:

```text
총 수입: 3000000원
총 지출: 15000원
잔액: 2985000원
예산: 500000원 (사용률 3.0%)

지출 TOP 3
1) food 15000원
```

해당 월에 데이터가 없는 경우 안내 메시지가 출력됩니다.

```text
[안내] 해당 월의 데이터가 없습니다.
```

---

## 8.5 예산 설정: `budget set`

월별 예산을 설정합니다.

```bash
python3 -m budget_app budget set --month 2024-01 --amount 500000
```

예시 출력:

```text
[저장 완료] 2024-01 예산 500000원
```

예산을 설정한 뒤 `summary`를 실행하면 예산 사용률이 함께 출력됩니다.

지출이 예산을 초과한 경우 경고 문구도 출력됩니다.

```text
[경고] 예산을 초과했습니다.
```

---

## 8.6 카테고리 관리: `category`

카테고리는 추가, 목록 조회, 삭제가 가능합니다.

### 카테고리 추가

```bash
python3 -m budget_app category add
```

실행 후 카테고리명을 입력합니다.

```text
카테고리명: coffee
```

성공 예시:

```text
[저장 완료] category=coffee
```

### 카테고리 목록 조회

```bash
python3 -m budget_app category list
```

예시 출력:

```text
- food
- transport
- rent
- salary
- etc
- coffee
```

### 카테고리 삭제

```bash
python3 -m budget_app category remove --name coffee
```

성공 예시:

```text
[삭제 완료] category=coffee
```

단, 이미 거래 내역에서 사용 중인 카테고리는 삭제할 수 없습니다.

```text
[오류] 이미 사용 중인 카테고리는 삭제할 수 없습니다.
```

이 프로젝트에서는 안전한 데이터 관리를 위해 사용 중인 카테고리 삭제를 막는 방식을 선택했습니다.

---

## 8.7 거래 수정: `update`

이 프로젝트는 옵션 기반 수정 방식을 사용합니다.

기본 형식:

```bash
python3 -m budget_app update --id TX-000001 [options]
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

예시:

```bash
python3 -m budget_app update --id TX-000001 --amount 20000 --memo "dinner"
```

성공 예시:

```text
[수정 완료] id=TX-000001
```

존재하지 않는 ID를 입력하면 다음과 같이 안내합니다.

```text
[안내] 해당 id의 거래가 없습니다: TX-999999
```

---

## 8.8 거래 삭제: `delete`

거래 ID를 기준으로 특정 거래를 삭제합니다.

```bash
python3 -m budget_app delete --id TX-000001
```

성공 예시:

```text
[삭제 완료] id=TX-000001
```

존재하지 않는 ID를 입력하면 다음과 같이 안내합니다.

```text
[안내] 해당 id의 거래가 없습니다: TX-999999
```

---

## 8.9 CSV 내보내기: `export`

조건에 맞는 거래 내역을 CSV 파일로 내보냅니다.

월 기준 내보내기:

```bash
python3 -m budget_app export --out export.csv --month 2024-01
```

기간 기준 내보내기:

```bash
python3 -m budget_app export --out export.csv --from 2024-01-01 --to 2024-01-31
```

성공 예시:

```text
[완료] export.csv (3 records)
```

`export` 명령어는 반드시 `--month` 또는 `--from`/`--to` 조건 중 하나 이상을 받아야 합니다.

---

## 8.10 CSV 가져오기: `import`

CSV 파일의 거래 내역을 일괄 등록합니다.

```bash
python3 -m budget_app import --from import.csv
```

성공 예시:

```text
[완료] imported=2, skipped=0
```

잘못된 행이 있으면 해당 행은 건너뛰고 `skipped` 개수에 포함됩니다.

---

## 9. Import / Export CSV 스키마

CSV 파일은 UTF-8 인코딩을 사용하며, 첫 줄에 헤더가 포함되어야 합니다.

| column | required | 설명 |
| --- | --- | --- |
| `date` | Y | 날짜, `YYYY-MM-DD` 형식 |
| `type` | Y | `income` 또는 `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 메모 문자열 |
| `tags` | N | 쉼표로 구분된 태그 문자열 |

CSV 예시:

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,lunch,meal
2024-01-16,income,salary,3000000,monthly salary,work
```

---

## 10. 입력 검증 및 오류 처리

프로그램은 다음과 같은 입력값을 검증합니다.

| 검증 항목 | 조건 |
| --- | --- |
| 날짜 | `YYYY-MM-DD` 형식 |
| 월 | `YYYY-MM` 형식 |
| 금액 | 0보다 큰 양수 |
| 거래 타입 | `income` 또는 `expense` |
| 카테고리 | 등록된 카테고리만 허용 |
| 거래 ID | 수정/삭제 시 존재 여부 확인 |

오류 발생 시 Python 스택트레이스를 그대로 출력하지 않고, 사용자에게 이해하기 쉬운 오류 메시지와 힌트를 출력합니다.

예시:

```text
[오류] 날짜 형식이 올바르지 않습니다. 예: 2024-01-15
[힌트] 입력값을 다시 확인하세요.
```

정상 종료 시 exit code는 `0`, 오류 발생 시 exit code는 `0`이 아닌 값으로 종료되도록 구현했습니다.

---

## 11. 설계 및 구현 포인트

## 11.1 제너레이터 기반 스트리밍 처리

거래 내역 파일은 제너레이터를 사용하여 한 줄씩 읽습니다.

```python
def iter_transactions(self) -> Iterator[Transaction]:
    with self.paths.transactions.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                yield Transaction.from_dict(data)
```

이 방식은 파일 전체를 한 번에 메모리에 올리지 않고 필요한 데이터만 순차적으로 처리할 수 있다는 장점이 있습니다.

따라서 거래 내역이 많아져도 메모리 사용량을 줄일 수 있습니다.

---

## 11.2 데코레이터를 활용한 공통 예외 처리

CLI 실행 중 발생할 수 있는 오류는 데코레이터를 통해 공통 처리했습니다.

```python
@handle_cli_errors
def main() -> int:
    ...
```

이를 통해 각 명령어마다 반복적으로 `try-except`를 작성하지 않아도 되고, 오류 메시지 출력 방식도 일관되게 유지할 수 있습니다.

---

## 11.3 타입 힌트 적용

함수와 클래스에는 타입 힌트를 적용했습니다.

예시:

```python
def validate_amount(amount: int) -> int:
    ...
```

```python
def add_transaction(...) -> Transaction:
    ...
```

타입 힌트를 사용하면 함수가 어떤 값을 입력받고 어떤 값을 반환하는지 명확해져 코드 이해와 유지보수가 쉬워집니다.

---

## 11.4 dataclass 기반 데이터 모델

거래 내역과 예산 정보는 `dataclass`를 사용해 정의했습니다.

예시:

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

이를 통해 데이터 구조를 명확히 표현하고, 객체와 딕셔너리 변환도 쉽게 처리할 수 있습니다.

---

## 11.5 update/delete의 안전한 파일 처리

파일 기반 저장 방식에서는 기존 데이터의 일부만 직접 수정하기 어렵기 때문에, 수정과 삭제는 다음 방식으로 처리했습니다.

```text
1. 기존 파일을 한 줄씩 읽는다.
2. 수정/삭제 결과를 임시 파일에 쓴다.
3. 임시 파일을 기존 파일로 교체한다.
```

교체에는 `os.replace()`를 사용했습니다.

```python
os.replace(temp_path, self.paths.transactions)
```

이 방식은 기존 파일을 직접 수정하는 것보다 안전하며, 파일 처리 중 문제가 생겨도 데이터 손상 가능성을 줄일 수 있습니다.

---

## 12. 구현한 필수 기능 체크리스트

| 기능 | 구현 여부 |
| --- | --- |
| 거래 추가 `add` | 완료 |
| 거래 목록 `list --limit` | 완료 |
| 거래 검색 `search` | 완료 |
| 월별 요약 `summary --month --top` | 완료 |
| 예산 설정 `budget set` | 완료 |
| summary에서 예산 사용률 출력 | 완료 |
| summary에서 예산 초과 경고 출력 | 완료 |
| 카테고리 추가 `category add` | 완료 |
| 카테고리 목록 `category list` | 완료 |
| 카테고리 삭제 `category remove` | 완료 |
| 사용 중 카테고리 삭제 방지 | 완료 |
| 거래 수정 `update --id` | 완료 |
| 거래 삭제 `delete --id` | 완료 |
| CSV 가져오기 `import --from` | 완료 |
| CSV 내보내기 `export --out` | 완료 |

---

## 13. 기술 요구사항 체크리스트

| 요구사항 | 적용 여부 |
| --- | --- |
| Python 3.10 이상 | 적용 |
| 표준 라이브러리만 사용 | 적용 |
| 외부 패키지 미사용 | 적용 |
| 최소 3개 이상 모듈 분리 | 적용 |
| 최소 2개 이상 클래스 사용 | 적용 |
| dataclass 사용 | 적용 |
| 타입 힌트 사용 | 적용 |
| 제너레이터 `yield` 사용 | 적용 |
| 데코레이터 사용 | 적용 |
| 데이터 3개 이상 파일로 저장 | 적용 |
| `transactions.jsonl` 저장 | 적용 |
| `categories.jsonl` 저장 | 적용 |
| `budgets.jsonl` 저장 | 적용 |
| update/delete 시 임시 파일 및 `os.replace()` 사용 | 적용 |
| 오류 시 스택트레이스 미출력 | 적용 |
| 오류 발생 시 non-zero exit code 반환 | 적용 |
| README 작성 | 적용 |
| 명령어 예시 포함 | 적용 |
| 저장 파일 위치 및 형식 설명 | 적용 |
| import/export CSV 스키마 포함 | 적용 |

---

## 14. 실행 테스트 예시

아래 순서로 실행하면 주요 기능을 확인할 수 있습니다.

```bash
python3 -m budget_app category list
```

```bash
python3 -m budget_app category add
```

```bash
python3 -m budget_app add
```

```bash
python3 -m budget_app list --limit 5
```

```bash
python3 -m budget_app search --category food
```

```bash
python3 -m budget_app budget set --month 2024-01 --amount 500000
```

```bash
python3 -m budget_app summary --month 2024-01 --top 3
```

```bash
python3 -m budget_app update --id TX-000001 --amount 20000 --memo "dinner"
```

```bash
python3 -m budget_app delete --id TX-000001
```

```bash
python3 -m budget_app export --out export.csv --month 2024-01
```

```bash
python3 -m budget_app import --from import.csv
```

---

## 15. 마무리

이 프로젝트는 단순히 수입과 지출을 저장하는 프로그램이 아니라, 파일 기반 저장소를 사용하는 작은 콘솔 서비스입니다.

거래 내역, 카테고리, 예산 데이터를 분리하여 저장하고, 제너레이터를 통해 데이터를 스트리밍 방식으로 처리하며, 데코레이터와 타입 힌트를 활용해 코드의 안정성과 유지보수성을 높였습니다.

또한 수정과 삭제 과정에서는 임시 파일과 원자적 교체 방식을 사용하여 파일 기반 프로그램에서 발생할 수 있는 데이터 손상 위험을 줄였습니다.