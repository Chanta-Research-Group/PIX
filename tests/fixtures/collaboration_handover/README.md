# Two-organization handover mapping oracle

This fixture exercises existing PIX public operators. It does not add a PIX
engine API, a Pida profile, a deployed remote adapter or desktop acceptance.
Run from the PIX checkout with its `src` on `PYTHONPATH`:

```sh
python examples/collaboration_handover_demo.py --fixture tests/fixtures/collaboration_handover --output /absolute/new-output
python -m pytest -q tests/test_collaboration_handover_consumer.py
```

Output must be a new directory. The example also reads
[current_cut](../current_cut/README.md) and `examples/current_cut_demo.py`;
copy those dependencies too when moving it. It is a repository example rather
than an installed-wheel acceptance check.

## Three distinct evidence sources

| File | Status and meaning |
| --- | --- |
| `local_projection.json` | Hand-authored semantic projection of Schumpeter PR8 `237417a5e5742888f565b30581387c7a2833a7f3`; real qualifier meanings, synthetic IDs/times. Not captured exporter bytes. |
| `pida-envelope-v1.json` | Exact golden wire fixture copied from Pida owner work at base `30fef192b478b1697bb95a22ad7340cf1c485b03`; new local file, not claimed committed there. SHA-256 `ee7386c009799ac52b976b26c99b45b4fceae4dc78338581045da8c71aebfdfe`. |
| `input.json` | Proposed synthetic remote observation mapping and separate synthetic case journal. No remote dispatch capture or live receipt is claimed. |
| `expected.json` | Independently specified counts, links, unresolved states and costs. Generated native results are evidence, not the oracle. |

Pida subsequently froze the same wire bytes in local commit
`50d1ed49294cb8acfabb00badd72da6877e22c30` (not pushed). Its owner reports focused
delivery tests, with full-suite failures still unresolved. No producer suite
result is counted in this PIX test run. Pida's wire fixture has a valid canonical envelope payload digest
`b3e9a68120885e6a91cec1062c718899a0cd2e22f5d6c8d46e222df30cfd0edd`.
It has no `job_id`, dispatch timestamp or case sequence. The inspected
`src/collaboration.ts` bytes had SHA-256
`83c89b003ea3c85fd8420497fd296e0d5ed49d381ba47a0edc58ef08ad588729`.
That was the initial inspected helper hash. After the owner added a plain-object
domain check and committed, the helper hash became
`af264d0477c52b5243c5e3c6dd77713f11aa7cd29ed62062754570f597a941b2`.
This fixture only checks the unchanged wire bytes/digest and field distinctions.

## Existing Schumpeter local contract

The inspected source is `src/schumpeter/collaboration.py` and
`collaboration_cli.py` at the PR8 revision above:

- `message.post`: message `sent`, sender organization `sender`, intended
  organizations `recipient`. Intended recipients do not establish receipt.
- `message.receipt`: same message `received`, recipient organization `recipient`.
  This is a local-host delivery observation, not remote execution or model input.
- A reply uses its own message ID and a `responds_to` relation. That relation
  does not fabricate the reply's receiver event.
- `contract.submit`: exact raw-byte digest as `artifact_revision` / `submitted`.
  `contract.review`: those revisions / `evaluated`, criterion digest /
  `evaluated_against`, acceptance review digest / `records`.

The local handover call is `HandoverSpec(actor_object_type="organization",
sender_qualifiers=("sender",), receiver_qualifiers=("recipient",),
time_precision=TimePrecision(1, attribute="time_granularity_microseconds"))`.
Expected: one request link and one unmatched answer send. One review event
retains both exact artifact digests, criterion identity and acceptance reference.
PIX does not recompute the business acceptance from that reference.

Actual Schumpeter exports namespace raw object refs with source ID and then
encode native IDs in `pix_port.project`. This semantic fixture uses readable
IDs; a consumer check must compare its declared mapping/lineage, not assume its
native computation digest or object-ID spelling equals this fixture's. Artifact
and criterion bytes here are synthetic, not Schumpeter's canonical review encoding.

## Proposed remote observation contract

External carrier identity within an authenticated owner scope is the tuple
`(producer_id, request_id, recipient.organization_id)`. The example represents
`(authenticated_owner_scope, producer_id, request_id, recipient.organization_id)`
as `message:` followed by a compact JSON array, avoiding delimiter and cross-owner
collisions. Missing owner scope fails; a test proves two owner scopes produce
disjoint carrier identities. The host must supply that scope from authentication,
never from an untrusted sender field. The synthetic input declares a fixture
scope for this test, which is not authentication or permission enforcement.

| Observation | E2O | Evidence required |
| --- | --- | --- |
| Explicit dispatch observation | carrier `sent`, participant `sender` | A real sender-side event/source reference and observed time. Envelope existence alone is insufficient. |
| Pida receipt `phase=job_enqueued` | same carrier `received`, participant `receiver` | Receipt ID, exact native job ID, matching envelope digest/recipient and `received_at`. This states durable enqueue only. |
| Runtime context inclusion / local acceptance | participant `actor`, no carrier handover role | Keep its own source evidence. It cannot substitute for receipt or task success. |

The remote `HandoverSpec` uses `collaboration_participant`, sender/receiver
qualifiers, and grouping by a declared immutable `organization_id` binding.
Participant IDs represent exact organization/host/session/agent/binding snapshots;
neither UUID shape nor current membership lookup justifies historical grouping.
All five binding fields are retained as participant OCEL attributes. An unchanged
participant ID does not imply an unchanged binding: changing host, native session,
agent or binding revision changes native source/computation identity even when
the handover counts remain equal. Consumers must re-evaluate applicability, not
reuse an old result because its numeric answer happens to match. This retention
does not authenticate the binding or resolve temporal membership.
Changing membership is rejected by the native grouping operator rather than
collapsed into the newest organization. This spec must have a distinct consumer
configuration/cache identity from the local organization spec.

`job_id` binds execution mapping; it is not external message identity.
Payload mismatch under the same carrier fails mapping. Different producer,
request or recipient does not join even when job labels, bytes or times match.
An absent send leaves an unmatched receive. Duplicate event/cut/source positions
and conflicting receipt bindings fail rather than repairing evidence.

The synthetic input order puts the request receipt last; its source-local
receipt position is 0 and observed time precedes send by one second. The early
cut lacks that receipt; the late cut joins it by identity and retains the clock
conflict. It never retimestamps or infers global causal order. A second producer's
same request label and payload stays unmatched. Context and acceptance events
interleave without becoming transport events.

Pida's actual receipt currently supplies `received_at` without source sequence.
Missing source positions stay absent in mapped OCEL. When present, positions
refer only to their named source journal; gaps in a cut are not renumbered.
They cannot become the online profile's per-case sequence. The separate
`sequential_source` fixture explicitly supplies its case sequence and close;
the test rejects gaps or a receipt-arrival sequence basis. This is synthetic
sequence evidence, not evidence that a live producer supplies it.

## Native outputs and oracle

The example publishes seven native result documents, five OCEL snapshots,
copied inputs and `run-record.json`. The record hashes every published artifact
and its source files; native result strings must retain exact bytes. Existing
current-cut models/fixtures remain pinned through their source hashes, not
silently reconstructed by a consumer.

- Early remote cut: response link only; request and pending sends unmatched;
  other producer's receive unmatched.
- Late cut: two links, one per organization direction; pending send and orphan
  receive remain unmatched; request time conflict is preserved.
- Online open case: cost 0, `partial`, final cost unresolved. Explicit completion
  stays `partial`; this proxy is not an exact arbitrary-DFG guarantee.
- Completed shared-artifact fixture: four synchronous moves, cost 0, verify
  once with both revisions. Independent reads have no added edge. Terminal
  alignment before verify has cost 1; it is not a live object-cut failure.

The last two use the existing current-cut oracle unchanged. Local byte-digest
artifacts and its opaque `artifact-a@r1` / `artifact-b@r7` identities are different
fixtures; no equality between them is inferred.

Falsify this proposal if an authorized source cannot bind these identities,
receipt semantics differ, independent reads acquire a causal edge, one shared
event is counted twice, unknown order is repaired, or a supported native result
disagrees with the hand oracle. Refresh after source/schema/profile changes.
The do-nothing alternative is to retain the already accepted batch/profile
paths until the remote source contract has the required evidence.
