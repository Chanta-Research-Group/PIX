# Schumpeter PIX 소비 준비 검증 보고

기준일: 2026-10-25 KST. 범위: PIX-01~07, PIX 측 X0~X5.

**PIX의 독립 설치·소비 계약 검증을 완료했다. Schumpeter 실제 소비 환경의 G1 검증은 아직 확인하지 않았다.** 현재 필수 fixture는 기존 엔진으로 처리되므로 ADP-01 범용 provenance API와 ADP-02 새 시간 구간 선택자는 구현하지 않았다. 기존 chat adapter, 기본 결과 identity와 공개 API를 유지했다.

## 1. 기준 버전과 변경

| 항목 | 값 |
| --- | --- |
| 작업 브랜치 | `work-pix-hub-readiness-20261025` |
| 검증한 구현 커밋 / 권장 Pin | `70df30ac38a11ba40536447f33d0fb1a93669418` |
| 구현 tree | `b3273eea8eb227db462aee01ed9b77cdf8e50e4c` |
| 기존 main / PR #12 병합 | `48fe7eb67388cda1144c5bba93adbfe00933ab1c` |
| PIX 패키지 | `0.5.0`, Python 지원 선언 `>=3.10` |
| 로컬 검증 | Linux, Python 3.12.14; pytest 9.1.1, ruff 0.17.2, openpyxl 3.1.5, pyarrow 26.0.0 |
| 결과 형식 | `pix.analysis-result` 1.3.0, 기존 1.0–1.2 읽기 회귀 포함 |
| 로컬 wheel SHA-256 | `c041c8e690800acf841776aae3164eb5630d2f9767fe85812e88ac4269bf7afe` |

`src/pix`와 `pyproject.toml`은 위 main과 동일하다. 새 커밋은 소비 예제·fixture·수락 테스트·문서·wheel 검증 및 CI 연결을 추가한다. 이 보고와 계획 상태 갱신이 뒤에 커밋되더라도, 위 SHA는 실제 실행한 코드/fixture 기준으로 유지한다. 패키지 버전 문자열만으로 원본 코드를 특정하지 않는다. GitHub release/tag 조회는 비어 있었으며, 임의의 외부 동명 패키지를 설치 기준으로 삼지 않았다.

이번에 수정한 실제 문제는 소비 예제 작성 중 확인한 호출 방식이었다: canonical digest 문자열은 `str(digest)`가 아니라 `.identifier`, E2O 근거 필드는 `event/object/qualifier`, drop 정책 값은 `drop_with_count`다. 이를 코어 결함으로 분류하거나 API를 바꾸지 않고 예제·Matrix에 반영했다.

## 2. 검증 결과

| 검증 | 결과 / 범위 |
| --- | --- |
| 기존 집중 기준선 | 837 passed, 17 skipped, 52 subtests; 선택 의존성 미설치 상태 |
| 최종 집중 검증 | **877 passed, 1 skipped, 52 subtests**; JSON/XML/SQLite 및 선택 포맷 의존성 포함. skip은 Windows junction 시험 |
| 신규 소비자 수락 시험 | **24 passed**; 공개 API만 사용, F01~F09의 부족한 연결·반례 보완 |
| 로컬 전체 Python 첫 실행 | 10,700 passed, 2 failed, 42 skipped, 1,169 subtests |
| 위 실패 2개 재검증 | **2 passed**. 검증 환경에 PIX 설치를 빠뜨려 subprocess에서 `No module named pix`가 발생한 환경 문제. CI와 같이 editable 설치한 뒤 해당 두 시험만 재실행; 제품 코드 수정 없음 |
| 설치 wheel의 소비자 수락 시험 | **24 passed**, source tree 밖으로 복사한 시험/fixture에서 `python -I -m pytest` 실행 |
| core-only wheel 검증 | mining·visualization 기존 검사 및 복사한 chat/adapter 예제 모두 통과. 실행 환경의 배포 패키지는 `pix==0.5.0` 하나, isolated=True |
| lint / 문서 | 변경 Python 파일의 ruff check/format, git diff whitespace, 문서 상대 링크 검사 통과 |
| 원격 CI | 검증 커밋의 [run 40151918609](https://github.com/Chanta-Research-Group/PIX/actions/runs/40151918609): **5개 작업 모두 success** |
| CI Python | Linux 3.10/3.12, macOS 3.13: 각각 **10,702 passed, 42 skipped, 1,169 subtests**. Windows 3.13: **10,703 passed, 41 skipped, 1,169 subtests** |
| CI browser / Node | **42 passed / 258 passed** |
| CI wheel | 4개 OS/Python 조합 모두 기존 wheel 검사와 두 copied example 통과; 같은 canonical digest 확인 |

로컬 첫 전체 실행을 “단일 실행 10,702개 통과”로 바꾸어 기록하지 않는다. 처음 2개 실패의 원인과 재검증을 구별했다. 로컬 browser 선택 시험은 실행하지 않았으며 CI의 browser 작업과 별도로 취급한다. PR #12 당시 통과 수치를 이번 결과로 재사용하지 않았다.

기계가 읽을 수 있는 실제 실행 정보는 [검증 근거 JSON](evidence/pi_hub_20261025.json)에 기록한다. 원격 CI가 제공하는 플랫폼별 실행 로그·artifact와 로컬 wheel hash는 구별한다. wheel 재빌드가 동일한 파일 hash를 만든다고 보장하지 않는다.

## 3. API와 재현 산출물

- [Consumer API Matrix](../user-guide/SCHUMPETER_PIX_CONSUMER_API_MATRIX.md): 공개 import, 입력·출력·옵션·상태·한계·최소 호출·검증 기준.
- [중립 fixture](../../tests/fixtures/pi_hub/README.md): 합성 입력, 매핑 선언, 수작업 기대값, F01~F10 검증 대응표.
- [외부 입력 예제](../../examples/adapter_contract_demo.py): public builder → 3종 OCEL 왕복 → 8개 native 결과 → 부모 artifact 연결.
- [수락 테스트](../../tests/test_pi_hub_consumer.py): ID 변경에 대한 의미 불변성, 불확실 시간, 외부 앵커, 무효 참조, 미연결·반복 인계, 빈/drop 입력 등.
- [wheel 검증](../../tools/validate_usage_wheel.py): 깨끗한 임시 환경에 wheel만 설치하고 두 예제와 fixture를 source tree 밖으로 복사해 실행. 기존 chat demo도 유지.

합성 기준 입력은 5 event / 5 object / 14 E2O / 1 O2O다. task 기준 1 execution / frequency 1 variant / DFG edge 4개, 간격은 60·60·60·30초다. A→B의 명시 carrier 인계 1건은 30초이며 60초 응답 제약을 충족한다. 같은 fixture의 JSON/XML/SQLite에서 canonical digest와 모든 native result bytes가 같다.

Canonical digest:

```text
pix.ocel.canonical.v1:sha256:108fbf5f7d6df53efd98fd5ae3351922bba0c485fcaf7d9bee0371a841854fed
```

예제 mapping digest:

```text
example.mapping.v1:sha256:bb6ed3edc2964bda5adf5b9bd4368e03f1c17c6e7508b6cc143372318d0dd05c
```

출력 bundle에는 입력/매핑/기대값, 3종 snapshot, traces·executions·variants·task_dfg·ocdfg·constraints·temporal·handover 결과와 run-record가 들어간다. 외부 매핑은 canonical 속성과 실행 기록으로 추적하고, 파생 결과는 부모 artifact를 연결했다. 따라서 채팅 전용 필드의 제거·통일이나 새 공통 provenance API가 이번 연결의 선행 조건은 아니다.

## 4. 설치와 재실행

권장 Pin은 위 구현 SHA 전체다. 해당 revision을 checkout한 소스에서 wheel을 만들고, Schumpeter의 잠금 파일/배포 기록에 실제 설치한 wheel hash를 함께 보관한다. 설치 경로·PIX 버전·환경을 확인한다.

```bash
python -m pip install -e '.[dev,imports]' build
python -m pytest tests/test_pi_hub_consumer.py tests/ocel tests/compute/test_time_precision.py tests/compute/test_handover.py tests/tabular/test_chat_log.py tests/test_results.py -q
python -m build --wheel
python tools/validate_usage_wheel.py --wheel dist/pix-0.5.0-py3-none-any.whl --output /tmp/pix-wheel-new --pix-commit 70df30ac38a11ba40536447f33d0fb1a93669418
```

사용한 모든 집중 시험 파일과 환경·수치는 검증 근거 JSON에 남긴다. 매번 새 출력 디렉터리를 사용한다. Schumpeter는 위 fixture 또는 자체 비식별 snapshot을 같은 API/spec로 실행하고 native 결과·coverage·환경 기록을 연결하면 된다. 실환경 승인은 Schumpeter 측에서 수행한다.

설치 wheel의 수락 시험은 별도 테스트용 venv에 wheel과 pytest를 설치하고, `tests/test_pi_hub_consumer.py`, `tests/fixtures/pi_hub/`, `examples/adapter_contract_demo.py`를 동일 상대 구조로 외부 디렉터리에 복사한 뒤 그 위치에서 다음 명령으로 재현한다. 이 테스트용 venv와 PIX만 설치한 core-only 환경은 구별한다.

```bash
python -I -m pytest tests/test_pi_hub_consumer.py -q --import-mode=importlib
```

## 5. 한계·책임·미해결 사항

| 사항 | 확인한 범위 / 담당 |
| --- | --- |
| concurrent 순차 분석 | 기존 거부 유지. 시간/일부 제약·인계의 불확실성은 계산하지만, 순차 discovery/alignment/replay/DFG 등을 지원한다고 확장하지 않음 |
| 외부 시간 구간 | 기존 앵커 속성으로 유한/미관측 상한을 처리하는 사례 통과. 완전 미관측 시간은 임의로 생성하지 않음. 새로운 일반 구간 API는 필요 시 후속 검토 |
| 원천 관측 누락 | PIX가 입력받지 않은 사건의 누락을 탐지했다고 주장하지 않음. Schumpeter가 원본 null·보류/제외·분모와 capture 범위를 기록 |
| UNKNOWN | 미확인 ID를 공통 실제 객체로 연결하지 않음. 소비자 관측 상태와 CR.unavailable의 뜻을 구별 |
| carrier 부재·반복 | timestamp로 연결하지 않음. 반복 관측은 현재 모든 송수신 조합이며 일대일 전달 확정이 아님 |
| verification | 검증 실행 이벤트·순서 계산은 artifact 버전의 독립 검증 성공이나 업무 완료 판정이 아님 |
| OCEL 표준 검증 | PIX semantic·round-trip 통과. 별도 reference-schema 검사 not_run을 공식 인증으로 표시하지 않음 |
| 실제 Schumpeter G1 | 아직 실행 근거 미제공. 대상 환경·snapshot/mapping·규범 모델·관측 정책으로 재실행 필요 |
| Provenance 운영 수락 | 실제 비정기 보고·현장 수락은 아직 없음. 보고가 오면 기존 접수 절차와 fixture에 연결 |

재현된 PIX 코어 결함은 없으며 현재 제품 코드 수정이 필요한 blocker도 확인되지 않았다. 이 결론은 위 시험 범위에 한정한다. WMC 수집기·권한·원장·운영 정책을 PIX에 추가하지 않았다. 변경된 CI는 동일 bundle의 독립 설치 검증을 앞으로 반복한다.

## 6. 요구·계획 상태

PIX-01~07의 PIX 측 문서·fixture·시험을 완료했다. X4는 “기존 엔진으로 충족, 제품 수정 불필요”로 종료한다. ADP-01/02는 조건부 후속 후보이며 구현 완료로 표시하지 않는다. X5는 PIX 인계 자료 준비까지 완료했고, Schumpeter 실환경/운영 수락은 별도로 남아 있다. 향후 Provenance 보고는 [접수 양식](../templates/PROVENANCE_PIX_REPORT_INTAKE.md)을 사용하되 자유 형식도 받는다.
