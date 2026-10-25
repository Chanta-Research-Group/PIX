# Schumpeter PI Hub 연동 준비 — PIX 검토 및 통합 패치 계획

작성일: 2026-10-25 KST

상태 갱신: 사용자 구현 지시에 따라 PIX 측 검증·예제·문서·설치 시험을 완료했다. [실행 보고](../reports/2026-10-25_SCHUMPETER_PIX_READINESS_REPORT.md)를 현재 상태의 기준으로 사용한다. ADP-01/02 확장은 검증 사례에 불필요하여 구현하지 않았고, Schumpeter 실제 G1 환경 검증은 미확인이다. 아래는 원래 계획과 당시 소스 검토 기록이다.

접수 문서: 사용자가 전달한 **PIX 개발 요구사항 — Schumpeter PI Hub Integration Readiness**, 기준일 2026-10-25, PIX-01~07 / X0~X5.

우선순위: High, Schumpeter G0-R/G1 연계.

제품 기준 main: `48fe7eb67388cda1144c5bba93adbfe00933ab1c`.

기존 계획 기준: `6997a9810ab6d85bd39ea4201448037ac513f7c8`, `work-pix-adapter-plan-20261025`.

## 1. 검토 결론과 기존 계획 조정

요구사항을 수용한다. 이번 범위의 목적은 이미 있는 PIX를 고정 버전으로 설치하여 Schumpeter가 정확히 소비할 수 있는지 입증하는 것이다. **검증 → 소비자 계약 문서화 → 재현 fixture → 필요한 최소 수정 → 인계** 순서로 진행한다. 최초 계획 작성 시에는 구현하지 않았고, 후속 사용자 지시로 실행했다.

[기존 ADP 계획](2026-10-25_PIX_ADAPTER_COMPATIBILITY_PATCH_PLAN.md)의 standalone 보존 조건은 그대로 유지한다. `import_chat_log`, `ChatLogMapping`, `ChatImportResult`, `MatchRule`, `CarrierRule`과 기존 예제·테스트를 제거하거나 폐기 예고하지 않는다. Schumpeter 설치·계정·네트워크 없이 PIX 단독 입력·분석이 가능해야 한다.

| 기존 항목 | 통합 계획에서의 처리 |
| --- | --- |
| ADP-00 기준선 | X0 최신 기준 확인과 X1 현재 동작 검증으로 확장 |
| ADP-01 범용 mapping provenance | X1/X3에서 기존 계보로 필수 추적이 안 되는 반례가 있을 때만 X4 후보로 채택 |
| ADP-02 공개 시간 구간 계약 | 기존 정밀도·앵커 표현과 문서로 필수 입력을 표현할 수 없을 때만 X4 후보로 채택 |
| ADP-03 외부 연동 예제 | ADP-01/02를 기다리지 않고 현재 API로 X3을 먼저 구성 |
| ADP-04 회귀·설치·인계 | 실제 변경 범위에 맞춰 X4/X5에서 수행 |
| Provenance 비정기 보고 | 기존 접수 절차 유지. 이번 요구 접수와 실제 운영 보고 접수를 구별 |

기존 코드가 요구를 충족하면 제품 수정 없이 문서·fixture·검증 기록으로 종료한다. 코드 구조 개선, 필드 통일, 새 알고리즘은 그 자체로 G1 선행 조건이 아니다.

## 2. 이번 계획 작성에서 확인한 사실

| 항목 | 확인 결과 | 증거 수준 |
| --- | --- | --- |
| 원격 main | `48fe7eb67388cda1144c5bba93adbfe00933ab1c` | 작성 시 GitHub branch 조회 |
| PR #12 | merged, merge SHA가 위 main과 같음 | [PR #12](https://github.com/Chanta-Research-Group/PIX/pull/12) 재조회 |
| Issue #11 | closed / `not_planned`, 2026-10-24 02:06:16 UTC 종료 | [#11](https://github.com/Chanta-Research-Group/PIX/issues/11) 재조회; API 부재의 뜻으로 해석하지 않음 |
| 저장소 패키지 버전 | `pyproject.toml`: `0.5.0`, Python `>=3.10` | 소스 선언 확인; 설치된 wheel·외부 패키지 인덱스의 최신판을 확인한 것은 아님 |
| GitHub Releases | 조회 결과 빈 목록 | tag/PyPI 배포 부재까지 의미하지 않음; X0에서 실제 배포 경로 확인 |
| 기존 CI | [40053859238](https://github.com/Chanta-Research-Group/PIX/actions/runs/40053859238), head `de140725daf064ffae20d1677d1c3193bd70b876`, completed / success | 당시 코드의 이력; 신규 G1 fixture 또는 소비자 환경 통과가 아님 |
| 제품 코드 변화 | 계획 브랜치의 기존 `6997a98`은 문서 변경 | 이번 제품 기준은 main과 동일; 계획 문서 SHA와 런타임 Pin SHA를 구분 |
| 결과 파일 | `src/pix/results.py`: 현재 `pix.analysis-result` 1.3.0 | 소스 확인; 기존 버전 읽기 회귀는 실행 단계에 재검증 |

이번에 실행한 것은 저장소·API·문서 읽기와 계획 문서 점검이다. 제품 테스트 수치·wheel 검증·Schumpeter G1 통과를 새로 보고하지 않는다. 과거 CI 결과를 이번 실행 결과로 복사하지 않는다.

## 3. 요구사항별 대응과 인수 기준

| 요구 | 현재 판단 / 주의점 | 실행 작업·산출물 | 인수 기준 |
| --- | --- | --- | --- |
| PIX-01 API 기준선 | 주요 API 존재. 공개 import 경로와 선행 계산이 다름 | X0/X2 Consumer API Matrix, 각 행의 최소 실행 예제 | 이름·입출력·범위·상태·옵션·한계·예제·검증 SHA 모두 기록 |
| PIX-02 OCEL 무결성 | builder, validator, I/O, canonical digest 존재 | X1/X3 관계·형식·timezone·출처·결정성 fixture | 유효 입력 보존, 잘못된 참조 진단, 지원 형식 round-trip, 원천/계산 identity 분리 |
| PIX-03 시간 | #9 재개발 불필요. 불확실성 지원이 연산마다 다름 | 동률·구간·확정 초과·정확 시각·ID 변경 반례 | 가능한 범위만 판정하고 미지원 순차 연산 명시 거부 |
| PIX-04 인계망 | carrier/qualifier 연산 존재 | fan-out·unmatched·충돌·group·ID 부재 fixture | 근거 E2O 추적, 시간으로 메시지 쌍 발명하지 않음 |
| PIX-05 채팅 mapping | #11 API 존재, 그대로 유지 | 규칙 identity·앵커·분류·drop·본문 옵션 검증 | 같은 입력/규칙 결정성, 결함의 원자적 실패/명시 수치, standalone 실행 |
| PIX-06 상태·계보 | native 필드와 외부 실행 기록의 책임 구분 필요 | 결과/부모 artifact 왕복·identity·coverage 검증표 | 모든 분석에서 적용된 입력·spec·버전·한계 추적, 모르는 값 조작 금지 |
| PIX-07 G1 fixture | WMC 문서의 공통 의미만 재사용 | PIX 중립 fixture와 소비자용 runner·예상값·명령 | 설치된 PIX에서 반복 실행, Schumpeter가 같은 fixture로 소비자 검증 가능 |

## 4. 소비자 API Matrix 초안 — 소스 확인, 실행 검증 전

아래 입출력은 기준 SHA `48fe7eb67388cda1144c5bba93adbfe00933ab1c`의 공개 export와 함수 선언에서 확인했다. **Verified commit은 아직 실행 미검증**이다. X2의 최종 Matrix에는 각 행에 실제 실행 SHA·환경·명령·결과 artifact를 붙인다.

`CR[T]`는 `ComputationResult[T]`, `CTX`는 `ComputationContext`를 뜻한다. 모든 API가 CR이나 같은 status enum을 반환하는 것은 아니다.

| 공개 API | 입력 → 출력 | 필수 선택 / 지원 범위·한계 | 최소 재현 항목 |
| --- | --- | --- | --- |
| `pix.ocel.build` | EventType/ObjectType/Event/Object/E2O/O2O iterable → `BuildResult` | 타입 선언·관계 명시. `valid`, `report`, `candidate`, 검증된 `ocel` 구분 | F01/F02: 유효·깨진 관계 각각 구성 |
| `pix.ocel.validate` | `OCEL` → `Report` | 데이터 의미·참조 검증; 원천 관측의 완전성 보장은 아님 | F02: 오류 위치·코드 확인 |
| `pix.api.read_ocel` | `Source`, 선택적 `format` → `OCEL` | 잘못된 입력은 예외 경로. 단계별 진단에는 공개 `pix.api.import_ocel`도 사용 | F01/F02: 파일 읽기·실패 진단 |
| `pix.api.export_ocel` | OCEL, path, 필수 `format` → `ExportResult` | JSON/XML/SQLite 프로필, 기본 overwrite 금지. 성공 `published`, 실패 `ExportError` | F01/F02: export/read/digest 비교 |
| `pix.ocel.canonical_digest` | OCEL, 선택적 canonical version → `CanonicalDigest` | 원본 파일 바이트 hash와 구별. import 메타데이터는 canonical 대상 아님 | F01/F09: 재배열·timezone·round-trip |
| `pix.api.reconstruct_traces` | OCEL/CTX, `TraceSpec` → `CR[TraceSet]` | object_type·qualifier·tie_policy·time_precision 명시 | F01/F03/F04 |
| `pix.api.discover_executions` | OCEL/CTX, `ExecutionSpec` → `CR[ExecutionSet]` | variant의 실제 선행 계산. method·객체 범위·tie 정책 필요 | F01/F05 |
| `pix.api.discover_variants` | `CR[ExecutionSet]`, `VariantSpec` → `CR[VariantSet]` | TraceSet 직접 입력이 아님. 완전한 execution·명확한 순서 필요; 정확 그룹화 한도 존재 | F01/F05: 선행 계산 포함 |
| `pix.api.discover_ocdfg` | OCEL/CTX, `OCDFGSpec` → `CR[ObjectCentricDFG]` | object_types 필수, qualifier·tie 정책. O2O는 directly-follows 간선 생성에 사용하지 않음 | F01/F05 |
| `pix.api.evaluate_constraints` | `CR[TraceSet]`, `ConstraintSpec` → `CR[ConstraintEvaluation]` | rule·open/closed 관측·window 선택. partial 상위 집단을 완전 판정하지 않음 | F03/F04/F09 |
| `pix.api.measure_temporal` | OCEL/CTX, `TemporalSpec` → `CR[ObservedTemporal]` | object_type·시간/동률 정책. service 측정은 관측된 start_attribute 필요 | F03/F04 |
| `pix.api.TimePrecision` | 정밀도 μs, alignment, 선택적 attribute → immutable spec | 계산 함수가 아님. 양의 정수 폭, aware timestamp, 반올림/순서 복원 안 함 | F03/F04: 생성·잘못된 설정 |
| `pix.api.discover_handover` | OCEL/CTX, `HandoverSpec` → `CR[HandoverNetwork]` | carrier/actor 타입·qualifier·수신자 정책·그룹 속성 선택 | F06/F07 |
| `pix.api.import_chat_log` | JSONL path 또는 records, `ChatLogMapping` → `ChatImportResult` | 선언형 규칙·위치·앵커·carrier 설정. ImportStatus 사용 | F08 |

최종 Matrix의 행별 필수 기록은 `API name / Input type / Output type / Supported scope / Result status / Required options / Known limitations / Minimum reproducible example / Verified commit`이다. 보조 `import_ocel`, `discover_executions`, `result_json_bytes`·`read_result` 등도 실제 실행 경로에 들어가면 함께 기록한다. `build`·`validate`·`canonical_digest`를 `pix.api`에 새로 재수출하는 것은 이번 요구의 필수 수정이 아니다.

### 상태와 지원 범위의 정정

- CR은 `computed / partial / unavailable / invalid_input`를 사용한다. `computed` 안에도 확정 위반·`indeterminate`·unmatched가 있을 수 있다. `computed = 업무 성공`, `indeterminate = 항상 partial`로 매핑하지 않는다.
- `ChatImportResult`는 `ImportStatus`와 `import_issues`를 사용한다. OCEL build/validate는 report, read는 반환/예외, export는 publication 상태를 사용한다. 전부 CR로 감싸기 위한 제품 API 재설계를 하지 않는다.
- `ExecutionSpec`에는 현재 `TimePrecision`/`concurrent` 선택이 없고, `OCDFGSpec`에도 time_precision 필드가 없다. API 존재만으로 구간·분 정밀도 전체를 지원한다고 표시하지 않는다. X1에서 지원 경계를 검증하고, 불확실 입력은 소비자가 해당 분석을 명시적으로 보류하도록 한다.
- 초까지 표시된 timestamp와 초 단위 관측 구간은 다르다. 정확한 점 시각의 대조군은 기존 exact 의미를 사용하고, `TimePrecision(1_000_000)`을 선택한 초 단위 관측은 `[t, t+1초)`로 검증한다. 문자열의 자릿수만 보고 정밀도를 추정하지 않는다.
- `discover_variants`는 object-centric execution 동등성 계산이다. 사용자가 기존에 쓰던 Trace의 `value_counts()` 카탈로그·상위 20% 선택과 구별한다. 이번 연동으로 기존 카탈로그 의미를 변경하지 않는다.
- `concurrent`의 내부 표시 순서·event ID·source position은 실제 선후 증거가 아니다. DFG/OCDFG·discovery·alignment·replay·prefix precision의 기존 거부를 유지한다. 불확실 입력을 `event_id` 정책으로 바꾸어 G1 성공으로 만들지 않는다.

## 5. 재현 fixture와 검증 설계

기존 테스트를 먼저 재사용하고, 누락된 소비자 연결·반례만 보완한다. 아래 ID는 계획상 사례 ID이며 현재 존재하는 파일·통과 결과를 뜻하지 않는다.

| ID | 입력·변형 | 기대 관찰 / 수작업 기준 | 요구 |
| --- | --- | --- | --- |
| F01 | 중립 Task 1, Agent A 시작→artifact 생성→verification 실행→송신→B 수신; 명시 ID와 정확 시각 | builder→I/O→trace/execution/variant/OCDFG→제약/시간/인계의 정상 경로. task/actor/carrier별 E2O와 선택한 O2O 보존 | 01/02/04/06/07 |
| F02 | 없는 object/event 참조, 잘못된 선언·중복 ID, qualifier·O2O 방향·event/object 속성, naive timestamp | 유효 관계는 round-trip 보존; 무효 입력은 오류 원인·위치 확인, 조용한 삭제·수정 없음 | 02 |
| F03 | 같은 분 송수신, lexical ID를 반대로 변경, 명시 순서를 알 수 없는 이벤트, 정확 초 관측 대조 | 연결 근거는 carrier, 순서는 불확실할 수 있음. bounds·불확실 판정은 ID 이름에 의존하지 않음 | 03/04 |
| F04 | 시간 window를 가로지르는 구간, 확실한 초과, 유한 앵커, 상한 없음, 선행 앵커 없음, open/closed 관측 | indeterminate/위반/pending 등 계약별 판정, 상·하한 보존. 전혀 모르는 시각은 유효 OCEL로 조작하지 않음 | 02/03/05/06 |
| F05 | concurrent Trace와 순차 연산, execution의 tie/partial 입력, 정밀도 미지원 경로 | 명시 거부·한계가 기대 결과. 확정 순서인 대조군만 variant/OCDFG 성공 기준에 사용 | 01/03/07 |
| F06 | A→B, A→C와 B→C, 다중 수신, 수신 없는 송신, 송신 없는 수신, 확정 시간 역전, 같은 분 | 각 link의 원 E2O, unmatched, order_conflicts, latency bounds 보존. 반복 송수신은 현재 모든 조합 의미 | 04 |
| F07 | carrier ID 부재, event_roles, 선택적 순서 매칭, 고정/변하는 그룹 속성, link 한도 | ID 없는 것을 timestamp로 결합하지 않음. event_roles는 별도 의미·latency 한계. 모호한 매칭/그룹·한도는 명시 진단 | 04/05 |
| F08 | 같은 records/규칙 반복·입력 순열, 규칙 변경, explicit carrier, 미분류/drop, malformed/중복 위치/한도, 본문 옵션 | mapping_digest·OCEL 결정성, 규칙 변경 반영, unclassified/dropped/anchored/turn/rule_hits 및 unmatched의 실제 제공 위치 기록 | 05 |
| F09 | 결과 재실행·JSON 왕복, 부모 결과 연결, 입력/spec 변경, 빈/전부 drop/일부 제외 입력, 결과 identity 변조 | 같은 기준에서 identity·native 결과 재현, 변경 시 적절한 identity 변화, 빈 입력 계보 보존, 부분 집단을 전체로 승격하지 않음 | 02/06/07 |
| F10 | source tree 밖 새 환경에서 wheel 설치 후 F01~09와 기존 chat demo | PIX만으로 실행, import 위치·버전·wheel hash 확인, Schumpeter·런타임·계정 불필요 | 01/07 |

검증의 세 가지 비교 기준을 구별한다.

1. **동일 입력 반복:** canonical digest, spec, computation ID, status/value 및 native result bytes를 반복 비교한다. 생성 시각·경로가 포함될 수 있는 외부 실행 기록은 별도 비교한다.
2. **의미 보존 변환:** 입력 순열·동일 instant의 timezone 표현은 canonical 의미를 비교한다. 서로 다른 I/O 형식의 파일 hash가 같아야 한다고 요구하지 않는다. 선택된 형식에서 PIX semantic/round-trip 검증과 공식 reference schema 검증 여부를 각각 기록한다. `reference_schema=not_run`을 표준 인증 통과로 표시하지 않는다.
3. **event ID 변경:** 의미상 판정·범위·개수는 같고 근거 ID는 대응표에 따라 바뀌어야 한다. ID가 canonical 입력에 포함되므로 source_digest/computation_id까지 같아야 한다고 요구하지 않는다.

정확한 시간 경계 포함 여부, 시간차의 하한·상한, 대상 객체·분모·관측 종료 시점을 fixture 설명에 적고 수작업 기대값을 고정한다. 새 출력으로 기대값을 자동 갱신하여 테스트를 통과시키지 않는다. 정상/거부/부분/불확실 결과는 모두 계약에 맞으면 수락 가능한 시험 결과다.

## 6. PIX-06 계보 및 coverage의 실제 책임

| 요구 필드 | 기존 PIX 표현 / 기록 위치 | 검증·보완 원칙 |
| --- | --- | --- |
| source_digest | CR.source_digest; canonical OCEL identity | 원천 파일 digest와 다른 이름·의미로 기록. 유효 입력 identity가 없으면 None 가능 |
| mapping_digest | ChatImportResult.mapping_digest; 비어 있지 않은 chat OCEL의 `pix:chat_mapping_digest`; 일부 결과의 `source_mapping_digest` issue | 모든 CR의 독립 필드라고 가정하지 않음. 빈/drop 및 파생 결과까지 부모 artifact·외부 실행 기록으로 추적 가능한지 확인 |
| pix_version / pix_commit | 배포·설치 및 실행 기록 | native 결과에 이미 있는 필드라고 주장하지 않음. wheel metadata, 검증 commit, wheel hash로 소비자가 결합 |
| operator / operator_version | CR.operator_id / operator_version | 이름을 맞추기 위한 중복 제품 계약 신설 금지 |
| spec / computation_id | CR.spec / computation_id | 입력·spec·연산자 버전·부모 identity의 관계 검증; ID만으로 실행 바이너리 버전을 안다고 주장하지 않음 |
| result_status | CR.status 또는 각 I/O API의 별도 상태 | 상태를 보존하고 소비자 표시 의미를 문서화 |
| result_artifact | result_json_bytes / write_result 등 기존 결과 codec | 외부 저장 위치·byte hash는 Schumpeter가 관리. 부모 artifact도 함께 보존 |
| known_limits / issues | CR.issues, I/O report/import_issues, 문서상 지원 한계 | issues가 모든 제품 한계를 자동 포함한다고 가정하지 않음 |
| 관측 coverage | 입력/제외·보류 수, open/closed 정책, 수집 범위의 소비자 기록 | PIX에 들어오지 않은 자료의 누락을 PIX가 알아냈다고 주장하지 않음 |

Schumpeter의 기존 실행·증거 기록 계약에 위 값을 연결한다. PIX에 WMC `ObservationEnvelope`·`ResultManifest` 복제본이나 별도 저장 서버를 만들지 않는다. provenance는 hash 존재만으로 인증·독립 검증·임무 완료를 보장하지 않는다.

`UNKNOWN`은 소비자의 미관측 의미이고 CR의 `unavailable`은 해당 계산 결과를 제공할 수 없다는 상태다. 미확인 `task_id/session_id/run_id`를 공통 객체 ID `"UNKNOWN"`으로 합쳐 서로 다른 업무를 연결하지 않는다. source ID는 namespace와 원 ID 대응을 보존한다.

유효한 부분 snapshot에 PIX가 `computed`를 반환해도 원천 전체가 관측됐다는 뜻이 아니다. 소비자는 원래 집단·분모·미투영 건수·이유를 유지한다. 증거가 없는 것을 위반 0건이나 완료 승인으로 바꾸지 않는다. raw `occurred_at:null`은 외부 원장에 보존하고, 근거 있는 앵커 투영 또는 명시적 보류만 허용한다.

## 7. 실행 순서, 예상 변경 파일, 종료 조건

아래 새 경로는 제안이며 아직 생성된 실행 산출물이 아니다. 기존 관련 문서·예제를 재사용할 수 있으면 중복을 만들지 않는다.

| 단계 | 작업 | 예상 산출물·파일 | 통과 조건 |
| --- | --- | --- | --- |
| X0 | main/work/PR·공개 API·배포·CI 상태 재확인 | 기준표, 설치 Pin 후보, 기존 테스트 대응표 | HEAD·코드 SHA·패키지·결과 형식·미확인 배포 경로 구별 |
| X1 | OCEL·시간·인계·채팅·계보의 기존 시험 실행 및 빠진 반례 추가 | 기존 tests/ocel, tests/compute, tests/tabular, tests/test_results.py; 필요 시 중립 통합 테스트 | F01~09의 지원/거부/한계가 계약대로 재현. 공백은 구체적 최소 사례로 기록 |
| X2 | 소비자 계약 확정 | `docs/user-guide/SCHUMPETER_PIX_CONSUMER_API_MATRIX.md` | 각 API의 요구된 9개 정보와 실제 실행 증거 완비; 실행 미확인은 명시 |
| X3 | 동일 자료를 재실행 가능한 bundle로 구성 | `tests/fixtures/pi_hub/`, `tests/test_pi_hub_consumer.py`, `examples/adapter_contract_demo.py`, fixture README | 중립 input/spec/기대값/실행 명령, ID·관계·coverage 설명. 기존 chat demo 유지 |
| X4 | 필요한 경우에만 최소 수정 | 실제 결함 파일과 회귀 테스트; ADP-01/02 중 필요한 부분 | 수정 전 실패·수정 후 기대 동작, 기존 계약 회귀 없음. 필요 없으면 “제품 변경 불필요”로 종료 |
| X5 | 설치 검증과 소비자 인계 | `docs/reports/2026-10-25_SCHUMPETER_PIX_READINESS_REPORT.md`(실행일이 달라지면 날짜 수정), wheel/실행 기록·Pin·잔여 제한 | F10, 최종 코드 SHA의 검증 근거, Schumpeter에서 재실행 가능한 명령·미해결 목록 |

X1에서 사용하는 작은 사례를 X3에서 정리해 공유한다. Matrix 작성이 모든 시험을 끝낼 때까지 막힐 필요는 없지만, 최종 지원 표시는 실행 근거가 있어야 한다. Schumpeter 전용 ingest→정규화→운영 판정 end-to-end는 Schumpeter 저장소에서 수행하고, PIX에는 중립 계약 fixture만 둔다.

### 기존 검증 재사용과 테스트 강도

집중 명령 후보는 다음과 같다. **이번 계획 작성에서 실행하지 않았다.**

```bash
python -m pytest tests/ocel tests/compute/test_trace.py tests/compute/test_executions.py tests/compute/test_variants.py tests/compute/test_ocdfg.py tests/compute/test_constraints.py tests/compute/test_temporal.py tests/compute/test_time_precision.py tests/compute/test_handover.py tests/tabular/test_chat_log.py tests/test_results.py tests/test_import_boundaries.py -q
python examples/chat_handover_demo.py --output /tmp/pix-chat-readiness
```

X3에서 신규 runner의 실제 옵션과 실행 명령을 확정한다. fixture만 보완하면 관련 집중 시험과 설치 시험을 수행한다. 공통 시간 계산·identity·codec·결과 계약을 수정하면 최종 통합 head에서 전체 Python suite와 관련 CI를 수행한다. UI를 바꾸지 않으면 UI 수동검증을 별도 추가하지 않는다.

각 구현 묶음의 통합 리뷰는 기본 1회다. 반려·수정된 항목과 그 영향 범위를 다시 검증한다. 공통 코드가 바뀌어 영향을 받는 기존 통과 결과는 그대로 재사용하지 않으며, 관련 회귀를 수행한다. 변경·실패·미해결 우려가 없으면 같은 전체 검사를 반복하지 않는다.

### X4 진입 조건

다음 중 하나가 최소 재현 입력으로 확인되어야 한다: (a) 필수 소비 계약을 기존 공개 API로 충족 불가, (b) 지원 문서와 다른 계산, (c) 결정성·계보·증거 손실, (d) 실제 버전 호환 차단.

진입 전 `요구 ID / fixture / 기대값 근거 / 실제 결과 / 기존 API·문서·소비자 수정으로 해결 가능한지 / 최소 변경 / 호환 영향 / 수락 시험`을 기록한다. 단순 사용 오류는 예제·문서를 수정하고, 원천 관측 부재는 수집 측 요구로 돌린다. ADP-01/02를 채택해도 legacy chat digest, 기본 computation identity, 기존 결과 읽기와 standalone API를 보존한다. 채택하지 않은 후보는 “불필요/보류”로 남기며 구현 완료로 표시하지 않는다.

## 8. Schumpeter와의 접점 및 Pin 정책

PIX 측은 합성 중립 자료로 즉시 검증 준비를 할 수 있다. 실제 소비 환경 검증에 필요한 다음 자료는 연결된 저장소·제공 자료에서 먼저 확인하고, 없는 부분만 Schumpeter 측 입력으로 남긴다.

- 실제 사용할 Python/OS·설치 방식·선택 의존성 및 고정하려는 PIX 배포물.
- 합성/비식별 OCEL snapshot과 생성 mapping·원천 ID 대응·시간/앵커 정책.
- 소비할 API/spec·대상 객체/qualifier·규범 모델·open/closed 관측·분모.
- 기대 결과와 그 근거, 제외/미관측 건수, 원천 샘플과 매핑의 버전.

기존 WMC 자료는 관측 조건의 참고다. `capture_mode` 값·activity enum 등 문서 간 불일치와 null/UNKNOWN 투영은 Schumpeter 매핑 단계에서 정합화해야 한다. PIX에서 제품별 enum을 허용하거나 `usage_exhausted`를 실제로 쓰지 않은 `stop_noted`로 바꾸어 해결하지 않는다. 단순 선행 관계만으로 최신 artifact 검증·독립성·최종 업무 성공이 입증됐다고도 해석하지 않는다.

**현재 검증 출발점 Pin 후보는 전체 SHA `48fe7eb67388cda1144c5bba93adbfe00933ab1c`다. 아직 G1 권장 확정 Pin이 아니다.** X5에서 실제 검증한 코드 SHA와 설치 wheel SHA-256을 함께 확정한다. 제품 수정이 없으면 기준 SHA를 유지할 수 있다. 수정이 있으면 검증된 수정 SHA를 사용한다. `main`, 계획 문서 커밋, `0.5.0` 이름만으로 실행 코드를 고정했다고 주장하지 않는다.

완료 판정은 두 단계다. PIX의 독립 설치·계약 시험 완료를 먼저 보고하고, 같은 bundle을 Schumpeter 소비 환경에서 재실행한 근거를 별도로 연결한다. 소비자 실행 근거가 없으면 **“PIX 측 준비 완료, Schumpeter G1 실환경 검증 미확인”**으로 남긴다. 이 상태를 전체 Hub 통합 완료로 승격하지 않는다.

## 9. 최종 보고와 후속 운영 보고

실행 후 보고에는 요청한 9개 항목을 모두 포함한다.

1. 현재 branch·HEAD·패키지 버전·wheel hash·환경.
2. PR #12 기능의 기존 CI 이력과 이번 실제 실행 결과의 구분.
3. API Matrix와 선택한 입력·spec·상태 계약.
4. OCEL / TimePrecision / Handover / Chat Mapping의 명령·통과·실패·skip·미검증 범위.
5. 불완전 입력, null, UNKNOWN/unavailable, concurrent, 분모·coverage 한계.
6. 재현된 결함과 수정 여부, 제품 변경이 없으면 그 근거.
7. 확정 권장 Pin SHA와 설치·검증 배포물의 연결.
8. fixture 입력·수작업 기대값·native 결과·실행 명령.
9. 변경 파일·테스트·commit/PR·미해결 사항 및 담당 프로젝트.

Provenance의 향후 비정기 보고는 [접수 양식](../templates/PROVENANCE_PIX_REPORT_INTAKE.md)과 기존 ADP 계획 §6으로 처리한다. 자유 형식 보고를 요구 ID·fixture·버전·기대값에 연결하고, PIX 결함/범용 요구/사용 문제/Schumpeter 운영/관측 한계로 분류한다. 실제 보고를 받으면 재현 사례를 재사용 가능한 회귀 자료로 발전시키되, 검토만 요청한 경우와 개발 보류는 따른다. 이번 계획을 미래 보고 접수·현장 수락·자동 모니터링으로 기록하지 않는다.

## 10. 범위와 근거

PIX 내부에 Runtime/LLM provider, scheduler, mission/delegation, 수집 서버/Hub 저장소, 조직 위계·인사·승인, persona memory, ContextPackage 정책, 자동 prompt/skill 진화, 근거 없는 최적 프로세스 추천을 추가하지 않는다. 기존 PIX 기능이나 다른 계획의 잔여 항목을 이번 문서로 제거·완료 처리하지 않는다. 의존 방향은 계속 Schumpeter → PIX다.

주요 소스: [공개 facade](../../src/pix/api.py), [OCEL 공개 API](../../src/pix/ocel/__init__.py), [실행/variant 계약](../../src/pix/contracts/execution.py), [공통 결과](../../src/pix/contracts/result.py), [결과 출처 처리](../../src/pix/compute/_common.py), [OCEL export](../../src/pix/ocel/export/writer.py), [기존 chat/time/handover 안내](../user-guide/CHAT_HANDOVER_AND_TIME_PRECISION.md).

아키텍처 경계는 사용자가 제공한 `PIX_PROJECT_CONTEXT_AND_ARCHITECTURE.md`의 단방향 의존과 소비자 운영 판정 분리를 따르되, 초기 v0.1 범위를 현재 기능 삭제 근거로 사용하지 않는다. WMC 자료의 검토 기준은 [Schumpeter PR #3](https://github.com/Chanta-Research-Group/Schumpeter/pull/3)의 기존 검토 SHA `084022bf9c34f3502b752aa3b9c24fc5df2ddf6f`와 `docs/pi-layer/` 자료다. 실행 착수 시 최신 변경을 재확인한다.
