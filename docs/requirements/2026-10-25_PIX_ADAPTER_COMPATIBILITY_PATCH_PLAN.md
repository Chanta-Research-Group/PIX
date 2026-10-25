# PIX 독립 사용성·어댑터 호환성 패치 계획

작성일: 2026-10-25 KST  
상태: 계획 작성 완료. 아래 제품 코드 패치는 미착수.  
기준 저장소: `Chanta-Research-Group/PIX`  
기준 main: `48fe7eb67388cda1144c5bba93adbfe00933ab1c` — PR #12 병합본  
계획 범위: 현재 채팅 입력 기능을 보존하면서 범용 계산 계약과 외부 연동 경계를 정리한다.

## 1. 이번 결정과 유지할 기준

**PIX는 Schumpeter 없이도 현재 수준의 입력·변환·분석 기능을 사용할 수 있어야 한다.** 채팅 어댑터를 제거하거나 다른 프로젝트로 강제 이전하지 않는다. `import_chat_log`, `ChatLogMapping`, `ChatImportResult`, `MatchRule`, `CarrierRule`과 관련 테스트·예제를 유지하고, 이번 작업에서 폐기 예고하지 않는다.

Schumpeter는 PIX를 재사용하면서 원천 수집, WMC 전용 정규화·운영 정책, 지속 저장, 승인·완료 판정을 추가한다. 의존 방향은 `Schumpeter → PIX`이며 PIX에 Schumpeter 설치·실행·네트워크 연결을 요구하지 않는다.

이 결정은 2026-10-25 검토 중 제안했던 “채팅 어댑터 전체 이관 후 PIX 공개 API 폐기”를 대체한다. WMC 문서의 R2 이관은 WMC 수집·운영 파이프라인의 소유권으로 해석한다. 기존 PIX 기능 제거의 근거로 사용하지 않는다. 다른 PIX 계획의 미완료 항목은 유지하며 이 문서에서 일괄 완료 처리하지 않는다.

사용자는 앞으로 WMC PI Scientist Provenance의 비정기 운영 보고와 개발 요구를 전달할 예정이다. 전달받은 자료는 검토·재현·분류한 뒤 후속 개발에 반영한다. 현재 요청은 이 계획과 접수 절차의 작성이며, 제품 코드 구현이나 정기 보고 자동화는 시작하지 않는다.

## 2. 확인한 구현과 계획상 변경

| 항목 | 기준 코드에서 확인한 상태 | 대응 |
| --- | --- | --- |
| 채팅 입력 | `src/pix/tabular/chat.py`: 선언형 턴·활동 규칙, JSONL/records, carrier 연결, 앵커, 원문 보존 옵션 | 공개 기능과 기본 동작 유지 |
| 표 입력 | `import_table`, `OCELTableMapping`, `mapping_fingerprint` | 기존 변환기를 재사용하며 별도 범용 importer를 중복 작성하지 않음 |
| 출처 정보 | `compute/_common.py`가 `pix:chat_mapping_digest`와 채팅 전용 설명을 직접 해석 | 명시적인 범용 출처 계약으로 정리, 구형 입력 호환 |
| 시간 구간 | `compute/_time.py`가 `time_basis=anchor_previous_observed`와 lower/upper 속성을 해석 | 기존 규약을 보존하면서 공개·검증 가능한 구간 선택 계약 추가 |
| #9 시간 정밀도 | `TimePrecision`, concurrent Trace, 불확실한 제약 판정·시간 범위 구현 | 재개발하지 않고 외부 어댑터 입력과 회귀 검증 |
| #10 인계망 | `HandoverSpec`, `discover_handover`, qualifier 근거·미연결·충돌·지연 범위 구현 | PIX에 유지, 객체 유형·qualifier 선택으로 외부 입력 수용 |
| 순차 연산 | concurrent Trace에 대한 DFG/OCDFG·discovery·alignment·replay·prefix precision의 거부 경로 | 지원 경계 보존. 부분순서 알고리즘 신설은 별도 요구 |
| 결과 파일 | 버전별 읽기와 identity 검증 경로 존재 | 구형 결과 읽기와 기존 기본 계산 identity 회귀 검증 |

근거 파일: [채팅 어댑터](../../src/pix/tabular/chat.py), [공통 결과 생성](../../src/pix/compute/_common.py), [시간 계산](../../src/pix/compute/_time.py), [사용 안내](../user-guide/CHAT_HANDOVER_AND_TIME_PRECISION.md).

위 내용은 소스 검토 결과다. 이번 계획 작성에서 제품 테스트를 다시 실행했다는 뜻은 아니다.

## 3. 책임 경계

| 처리 | PIX | Schumpeter / WMC |
| --- | --- | --- |
| 원천 취득 | 파일·records 등 이미 제공된 입력 읽기 | ReadTranscript/API 인증·수집, 페이지 커서, 재전송·지속 저장 |
| 채팅 변환 | 재사용 가능한 턴·활동 규칙, 명시적 메시지 연결·앵커링 | 실제 원천 형식에 맞는 규칙 구성, WMC 의미·업무 ID 연결 |
| 정보 범위 | 현재 원문 비보존 기본값과 오류 메시지 비노출 유지 | 반출 범위 결정, 민감 자료 제거, 접근 권한 |
| 수집 멱등성 | 입력 내 유효성·중복 검증과 결정론적 변환 | 소스 ID/이벤트 ID 원장, 재수신 영수증, 충돌 보존 |
| 시간 | 관측 정밀도·구간 검증과 범용 계산 | 관측 근거 확보, 앵커 선택, 원본 null 보존 |
| 인계 | 명시된 carrier/qualifier의 관계·지연 계산 | 실제 작업·메시지 식별, 추정 매칭 여부 표시 |
| 분석 | Trace·변형·제약·시간·인계망과 근거·한계 반환 | 대상 집단, 규범 모델, 운영 임계치 선택 |
| 의사결정 | 일반 계산 결과·진단 | 조직 위계, 승인, 업무 완료, 재시도·중단 판단 |

WMC의 `reported_direct`, `verification_passed`, COO/사내이사 등 역할과 운영 정책을 PIX 코어에 하드코딩하지 않는다. PIX의 범용 채팅 API가 존재한다는 것과 WMC 정책을 PIX가 소유한다는 것은 별개다.

## 4. 패치 순서와 완료 조건

| 순서 | ID | 패치 | 의존성 | 주요 완료 조건 |
| --- | --- | --- | --- | --- |
| 1 | ADP-00 | 현재 단독 사용·호환 기준 고정 | 없음 | 기존 입력, 출력, 공개 API, identity, 미지원 사례의 기준 확보 |
| 2 | ADP-01 | 변환 출처 정보 범용화 | ADP-00 | 채팅·표·외부 입력의 출처 전달, 구형 채팅 입력 호환 |
| 3 | ADP-02 | 시간 구간 공개 계약 | ADP-00 | 명시 구간 입력과 기존 앵커 입력의 의미·오류 처리 검증 |
| 4 | ADP-03 | 외부 어댑터 연동 경로 | ADP-01, ADP-02 | PIX만 설치한 환경에서 외부 정규화 입력을 분석 |
| 5 | ADP-04 | 통합 회귀·설치 검증과 인계 | ADP-01~03 | 기본 사용 회귀 없음, wheel 검증, 지원 범위·수정 SHA 기록 |

ADP-01과 ADP-02는 공통 기준 확정 뒤 독립적으로 설계할 수 있다. 통합 순서는 위 표를 따른다. 기능별 작은 커밋과 PR로 나누되, 작업 간 의존성 때문에 기능을 반쯤 제거한 상태를 병합하지 않는다. 기존 기능이 이미 요구를 충족하면 문서·검증만으로 해당 항목을 종료할 수 있다.

### ADP-00 — 현재 단독 사용·호환 기준 고정

대상: `tests/tabular/test_chat_log.py`, `tests/compute/test_time_precision.py`, `tests/compute/test_handover.py`, `tests/test_results.py`, `examples/chat_handover_demo.py`와 기존 fixture.

1. 착수 시 main/work 및 관련 PR을 재확인하고 변경된 기준 SHA를 기록한다. 다른 작업의 변경을 덮어쓰지 않는다.
2. 기존 테스트를 먼저 재사용한다. 빠진 실제 동작에 대해서만 합성 fixture를 보완한다.
3. 다음을 기준으로 고정한다: 공개 import·기본값, mapping digest, canonical OCEL digest, 기본 계산 identity, 원 event/object ID·qualifier, 시간·제약 결과, 구형 결과 파일 읽기.
4. 기본 채팅 입력, 시간 미관측·앵커, 명시 carrier ID, 선택적 순서 매칭, 미분류·잘못된 입력, concurrent 입력 거부를 포함한다.
5. Schumpeter 없이 `chat_handover_demo.py`가 입력→OCEL→Trace·인계망·시간/제약→결과 JSON까지 실행되는 기준을 확보한다.

완료: 뒤 패치가 바꿔도 되는 선택 기능과 그대로 유지해야 하는 기본 동작을 구분할 수 있다. 현재 스키마를 통과하지 못하는 입력을 새 기능 성공 사례로 기록하지 않는다.

### ADP-01 — 변환 출처 정보 범용화

주요 변경 대상: `src/pix/compute/_common.py`, `compute/context.py`, 관련 출처 계약/helper, `tabular/reader.py`, `tabular/chat.py`, 필요 시 `results.py`와 사용 안내.

권장 설계:

- 원천 내용 digest, 변환 mapping digest, canonical OCEL digest, computation ID를 서로 다른 항목으로 유지한다.
- 어댑터 공통의 명시적 mapping 출처 표현을 정의한다. 최소한 mapping identity와 이를 적용한 입력 범위를 추적할 수 있어야 한다. 정확한 필드명은 구현 전 fixture와 함께 고정한다.
- 기존 `pix:chat_mapping_digest`는 지원하는 구형 표현으로 유지한다. 기존 채팅 변환 결과에 새 속성을 무조건 추가해 snapshot digest를 바꾸지 않는다.
- 기존 `mapping_fingerprint`를 재사용한다. 서로 다른 mapping 형식의 해시를 동일 규칙의 해시라고 혼동하지 않으며 형식·버전을 식별한다.
- 공통 계산부는 정규화된 출처 정보를 소비한다. 구형 별칭 해석은 한 곳에서 담당하고 계산 연산마다 채팅 필드 탐색을 복제하지 않는다.
- 여러 mapping이 섞인 입력에서 하나를 대표로 임의 선택하지 않는다. 서로 충돌하는 정규·구형 값은 조용히 덮어쓰지 않고 명시적 진단을 반환한다.
- source provenance는 변환 이력이다. 해시 존재를 인증·독립 검증·완료 승인으로 승격하지 않는다.
- 기존 `OCELImportInfo`는 canonical identity 바깥의 메타데이터이므로, 의미를 바꾸는 mapping을 그곳에만 넣고 computation identity에서 누락시키지 않는다. 데이터 의미에 영향을 주는 설정은 입력 snapshot 또는 명시적 계산 spec에 반영한다.

검증: 같은 mapping의 반복 입력, mapping 변경, 여러 출처 혼합, 별칭 충돌, 출처 없음, 외부 generic input, 채팅 기본 입력 회귀, 결과 직렬화 왕복.

완료: 기본 채팅 입력의 기존 digest·identity를 보존하고, 채팅 이외 입력도 동일한 출처 전달 규약으로 분석할 수 있다. 잘못된 출처 정보 때문에 정상 결과처럼 보이는 상태를 만들지 않는다.

### ADP-02 — 시간 구간 공개 계약

주요 변경 대상: `contracts/time.py`, 시간 선택을 사용하는 spec, `compute/_time.py`, Trace·constraints·temporal·handover 소비 경로, 필요 시 `results.py`.

권장 설계:

1. 기존 `TimePrecision`의 정밀도 표현에 선택적 구간 속성 선택 계약을 추가하는 방향으로 설계한다. 신규 선택자는 기본값에서 비활성이며, 현재 API 호출과 기본 identity를 유지한다. 구체적 Python 필드명과 wire 표현은 ADP-00 fixture에 맞춰 고정한다.
2. 명시적 하한·상한 속성, 상한 미관측 처리, timezone·구간 유효성 검사를 공개 계약으로 문서화한다.
3. 기존 `time_basis=anchor_previous_observed` 표현은 계속 읽는다. 신규 명시 계약과 기존 앵커 표현이 함께 있으면 일치 여부를 확인하고, 불일치는 오류로 반환한다.
4. 근거가 있는 하한과 미관측 상한을 지원하되, 누락·역전·잘못된 타입을 임의의 정밀도 기본값으로 치환하지 않는다.
5. `Event.time`을 nullable로 바꾸지 않는다. 원천의 null을 수집 시각·0시·미세초 오프셋으로 메우지 않는다. 원본 null은 호출 측 원장에 유지하고, 계산용 앵커가 있는 경우에만 그 의미와 구간을 명시한다.
6. 하한조차 없는 사건은 이 계약으로 유효한 OCEL 사건이 된다고 주장하지 않는다. PIX는 명시적으로 거부하고, 호출 측은 보류·제외 수와 이유를 별도 기록한다. 부분 투영 결과를 전체 집단 판정으로 사용하지 않는다.
7. source position/turn sequence를 실제 시각이나 인과관계로 바꾸지 않는다. concurrent Trace의 순차 연산 미지원은 유지한다.
8. 새 선택 필드를 직렬화·identity에 추가할 때 기본값 생략 규칙과 기존 결과 읽기를 함께 검증한다. 필요하면 새 결과 형식을 명시적으로 버전 관리한다.

검증: 정확 시각, 분 단위 관측, 유한 구간, 상한 없음, 구간 역전, timezone 누락, 신규/구형 표현 충돌, 완전 미관측, open/closed 관측, 결과 파일 왕복. 사건 순서나 ID를 바꿔 불확실 판정이 확정으로 바뀌지 않아야 한다.

완료: 채팅 어댑터를 사용하지 않는 외부 입력도 공개 계약으로 같은 시간 의미를 전달할 수 있고, 기존 앵커 결과가 회귀하지 않는다.

### ADP-03 — 외부 어댑터 연동 경로

주요 변경 대상: 기존 `import_table`/OCEL builder 사용 예제, 사용자 안내, public API 및 통합 테스트. 예제 추가 위치는 `examples/adapter_contract_demo.py`를 제안한다. 아직 존재하는 파일로 간주하지 않는다.

1. 기존 채팅 예제를 유지한다. 별도 예제에서 외부 정규화 records/OCEL을 공개 builder 또는 표 mapping으로 입력한다.
2. 외부 어댑터는 원천 ID·활동·객체·qualifier·시간 의미·mapping 출처를 준비한다. PIX는 이 표현을 검증하고 계산한다.
3. `HandoverSpec`의 객체 유형·qualifier 선택을 사용한다. WMC 객체 이름을 맞추기 위해 PIX 기본값을 전역 변경하지 않는다.
4. 명시 carrier ID와 순서 기반 추정 연결을 구별한다. 동일 ID의 여러 송수신은 현재 모든 관측 조합이라는 의미를 유지하고 일대일 실전달 이력으로 과장하지 않는다.
5. `UNKNOWN` 문자열을 실제 공통 task/session ID로 만들어 서로 다른 업무를 합치지 않는다. 외부 어댑터 책임과 PIX의 입력 진단 범위를 예제에 명시한다.
6. 같은 의미의 최소 합성 자료를 채팅 경로와 외부 입력 경로에 넣어 활동·관계·계산 결과를 비교한다. ID/메타데이터가 다르면 전체 digest 동일성을 요구하지 않고 대응표와 차이를 설명한다.

완료: PIX만 설치한 환경에서 두 경로가 실행되고, Schumpeter import·WMC 계정·LLM·원격 서비스가 필요하지 않다. WMC ObservationEnvelope/ResultManifest 전체 스키마를 PIX 제품 API로 편입하지 않는다.

### ADP-04 — 통합 회귀·설치 검증과 인계

1. ADP-00 기준과 새 계약의 반례 테스트를 통합한다. 채팅·시간·인계·표 입력·공통 결과·codec·dependency 검증을 수행한다.
2. 공통 계산/identity/codec의 변경이 포함되므로 통합 head에서 전체 Python suite와 저장소 CI의 관련 검사를 실행한다. 변경하지 않은 UI의 수동 검증을 새로 의무화하지 않는다.
3. 소스 경로 밖의 깨끗한 wheel 환경에서 기존 채팅 예제와 외부 입력 예제를 실행한다. 입력·샘플 파일 외에 Schumpeter가 설치되지 않은 상태를 확인한다.
4. 사용 안내에 공개 API, 구형 별칭, null·구간·concurrent 한계, 입력·결과 버전, 실행 명령을 반영한다.
5. 검증 보고서에 실제 SHA·wheel hash·OS/Python·명령·통과/실패/skip·미검증 범위를 기록한다. 옛 테스트 수치를 새 head의 실행 결과로 사용하지 않는다.
6. PR 설명에는 PIX 단독 기능 보존과 WMC 운영 정책의 외부 소유권을 명시한다. 이번 계획 작성으로 코드 패치가 완료됐다고 표시하지 않는다.

완료: 설치된 PIX에서 현재 단독 사용 경로와 외부 어댑터 경로가 검증되고, 제한·호환성·후속 요구를 함께 인계한다.

## 5. 검증 매트릭스

| 사례 | 기대 판정 / 보호할 성질 | 담당 패치 |
| --- | --- | --- |
| 기존 채팅 JSONL과 기본 mapping | 공개 API·mapping/OCEL digest·기본 결과 identity 유지 | ADP-00/01/04 |
| 입력 순서만 바꾼 같은 source position | 기존 결정론 유지 | ADP-00/04 |
| generic mapping과 구형 chat digest | 둘 다 출처 전달, 중복·충돌 명시 | ADP-01 |
| 같은 분의 송수신 | 관계는 연결 가능, 순서·시간 의무는 필요한 경우 indeterminate | ADP-02/03 |
| 상한 없는 사건 | 유한 최대 지연을 만들지 않음 | ADP-02 |
| 시간 근거 전혀 없음 | 명시적 거부, 호출 측 보류·coverage 기록 | ADP-02/03 |
| 동일 carrier의 여러 송수신 | 현재 조합 의미·E2O 증거·한도 유지 | ADP-03 |
| unmatched/시간 역전/팬아웃 | 관계 보존 또는 선언된 거부, 숨은 보정 없음 | ADP-03 |
| concurrent Trace를 순차 연산에 전달 | 기존 미지원 진단 유지 | ADP-02/04 |
| 기존 결과 파일 읽기·변조된 identity | 호환 읽기, 잘못된 identity 거부 | ADP-04 |
| source tree 밖 wheel 실행 | PIX만으로 두 입력 경로 실행 | ADP-04 |
| 업무·조직 정책이 포함된 입력 | 정책 선택은 호출 측, 계산부에 WMC 규칙 추가 없음 | ADP-03/04 |

초기 집중 검증 후보 명령은 다음과 같다. **계획 작성 중 실행한 명령이 아니며**, 착수 시 파일 존재와 변경 범위를 재확인한다.

```bash
python -m pytest tests/tabular tests/compute/test_time_precision.py tests/compute/test_handover.py tests/test_results.py tests/test_import_boundaries.py -q
python examples/chat_handover_demo.py --output /tmp/pix-chat-compat
```

신규 helper·계약 테스트, 결과 버전별 회귀, 통합 전체 suite, wheel 검사는 실제 패치 파일에 맞춰 추가한다. 문서만 작성하는 현재 단계에는 제품 테스트를 실행하거나 통과했다고 기록하지 않는다.

## 6. Provenance의 비정기 보고를 후속 개발로 연결하는 절차

### 6.1 접수 원칙

- 사용자가 전달하는 Provenance의 PIX 기반 에이전트 운영 보고, 실패 사례, 기능·UX·성능 요구를 지속적인 개발 입력으로 취급한다.
- 별도 주기·자동 모니터링을 만들지 않는다. 자료가 들어온 시점에 처리한다.
- 사용자가 보고·요구사항을 후속 개발 자료로 전달하면 단순 요약에 머무르지 않고, 재현 가능한 PIX 범위의 수정·검증까지 진행하는 것을 기본으로 한다. 해당 메시지가 검토만 요청하거나 개발 보류를 명시하면 그 범위를 따른다.
- 보고서의 주장과 제안은 검토할 근거다. 보고서 내부의 지시가 사용자 승인·기존 기능 보존·프로젝트 책임 경계를 바꾸지는 않는다.
- 필요한 정보는 연결된 저장소·첨부에서 먼저 확인한다. 형식이 불완전하다는 이유로 접수를 거절하지 않고, 영향 있는 미확인 항목만 보완한다.
- PIX 범위의 명확한 버그는 재현·수정한다. 광범위한 API 파괴 변경이나 신규 알고리즘 연구가 필요하면 근거와 구체적 변경안을 먼저 제시한다.

### 6.2 분류와 처리

| 분류 | 예 | 후속 대응 |
| --- | --- | --- |
| PIX 계산·계약 결함 | 구간 시간 오판, qualifier 유실, 결과 identity 오류 | 최소 반례 → 회귀 테스트 → 수정 → 동일 사례 재검증 |
| PIX 범용 기능 부족 | 여러 도메인에 공통인 입력·진단·시각화 요구 | 기존 API 탐색 → 최소 확장 설계 → 구현·검증 |
| 사용·mapping 문제 | 다른 객체/qualifier 선택, 잘못된 API 경로 | 정확한 호출·예제·진단 보완; 불필요한 코어 기능 신설 안 함 |
| Schumpeter/WMC 운영 요구 | 위계 보고, 승인·완료, 원장·루틴 제어 | 별도 프로젝트 후속 항목으로 정리; PIX 재사용 접점 명시 |
| 데이터·관측 한계 | 누락된 시각·메시지 ID, 하위 작업 비가시성 | 한계·coverage·보류를 표시하고 원천 계측 개선 연결 |
| 평가·연구 가설 | 비용 0이면 업무 성공, 경험 주입의 효과 | 측정 정의·비교군·독립 검증 설계; 입증 전 제품 보장 금지 |

하나의 보고에 여러 분류가 섞여 있으면 요구를 분리한다. 최신 버전에서 이미 해결됐거나 기존 공개 API로 충족하면 근거와 재현 예제를 남기고 중복 개발하지 않는다.

### 6.3 보고에서 확보할 정보

간단한 원문도 접수한다. 아래는 접수 거절 조건이 아니라 추가로 확인할 목록이다.

| 정보 | 용도 |
| --- | --- |
| 원문·링크·작성 시점·분석 기간·수정 이력 | 원본 보존과 정정 추적 |
| PIX commit/패키지·Python/OS·의존성 | 동일 실행 기준 확보 |
| 비식별 최소 입력·digest·source/mapping 버전 | 재현·원천 오류 분리 |
| 사용 API·spec·규범 모델·time/tie 정책 | 의미·지원 범위 확인 |
| 실제 출력·status·issues와 기대 결과·수작업 근거 | 계산 결함 여부 판정 |
| 분자·분모·제외·pending/indeterminate·인프라 사건 | KPI 오해·오탐 방지 |
| 업무 영향·빈도·우회 가능성 | 우선순위 설정 |
| 희망 기능과 수락 사례 | 종료 조건 정의 |

원문 전체가 민감하면 합성 반례나 비식별 최소 자료를 사용한다. 계정 비밀·개인 맥락·원 대화 전문을 재현의 기본 요구로 삼지 않는다.

### 6.4 추적과 검증 종료

접수 번호는 `PRV-YYYYMMDD-NN`을 제안하며, 실제 보고가 들어올 때 발급한다. 항목별로 원문 → 재현 → 분류/owner → 패치/PR → 검증 근거 → 실사용 확인을 연결한다.

상태는 `접수 / 근거 보완 / 재현 확인 / 개발 대상 / 구현 중 / 기술 검증 완료 / 실사용 확인 / 보류 / 기존 기능으로 해결 / 다른 프로젝트 담당`을 구분한다. 기술 검증 완료와 Provenance의 운영 확인을 별도 기록한다. 후속 보고가 없다고 기술 작업을 무기한 멈추지는 않되, 현장 수락을 받았다고 표시하지 않는다.

우선순위는 (1) 잘못된 확정 판정·데이터 손실·기존 API 회귀, (2) 실제 분석을 막는 결함·호환성 문제, (3) 진단·반복 작업 개선, (4) 신규 연구·알고리즘 확장 순으로 정한다. 실제 업무 영향에 따라 조정한다.

접수 기록 양식은 [Provenance 보고·개발 요구 접수 양식](../templates/PROVENANCE_PIX_REPORT_INTAKE.md)을 사용한다. 보고서를 받을 때 기존 양식에 맞춰 정리하는 책임은 개발 측에도 있다.

## 7. 이번 범위에서 시작하지 않는 작업

- 채팅 기능 제거·폐기 예고, Schumpeter 의존성 추가.
- WMC 전용 관측 봉투 서버·원장·승인·루틴 제어 구현.
- 근거 없는 시각 복원, 일대일 인계 추정의 확정 취급.
- concurrent alignment 등 새로운 부분순서 알고리즘, 별도 근거 없는 시각화 확장.
- 대표 Trace 선정 알고리즘 변경, 기존 OCPM 잔여 항목의 일괄 완료 선언.
- Provenance 보고의 자동 수집·정기 일정·외부 메시지 발송.

## 8. 참고 기준과 현재 상태

- [PIX PR #12](https://github.com/Chanta-Research-Group/PIX/pull/12): #9/#10 및 현재 채팅 어댑터 구현 기준.
- [Schumpeter PR #3](https://github.com/Chanta-Research-Group/Schumpeter/pull/3), 검토 head `084022bf9c34f3502b752aa3b9c24fc5df2ddf6f`: WMC 연동 문서. 본 문서 작성 시 Draft이며 구현 완료 근거가 아님.
- [wmc-docs PR #2](https://github.com/Water-Mixing-Capital/wmc-docs/pull/2), 검토 head `5e7b79a8e5d33c5d343b596dc3376640c0a90faa`: 운영안·파일럿 보고.
- [2026-10-10 사용·인계 계획](2026-10-10_PIX_USAGE_AND_HANDOFF_PATCH_PLAN.md): 기존 비교·카탈로그 및 잔여 작업을 보존.
- [통합 실행 인덱스](2026-10-06_PIX_INTEGRATED_EXECUTION_PLAN.md): 기존 요구 추적을 유지.

현재 완료된 것은 이 계획과 접수 양식의 작성·문서 점검이다. ADP-00~04는 미착수이며, 새 보고 접수·제품 구현·테스트 통과·배포를 선언하지 않는다.
