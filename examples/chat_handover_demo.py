"""Synthetic conversation import -> qualified handover and uncertain timed response.

Run: python examples/chat_handover_demo.py --output /tmp/pix-chat-demo
"""

import argparse
import json
from pathlib import Path

from pix.api import (
    CarrierRule,
    ChatLogMapping,
    ConstraintSpec,
    HandoverSpec,
    MatchRule,
    TemporalSpec,
    TimedResponseRule,
    TimePrecision,
    TraceSpec,
    discover_handover,
    evaluate_constraints,
    import_chat_log,
    measure_temporal,
    reconstruct_traces,
    write_result,
)


def run(output):
    minute = TimePrecision(60_000_000)
    mapping = ChatLogMapping(
        time_precision=minute,
        turn_openers=(
            MatchRule("request", "role", "equals", "user"),
            MatchRule("received", "role", "equals", "incoming"),
        ),
        activity_rules=(MatchRule("sent", "tool", "equals", "send"),),
        carrier_rules=(
            CarrierRule(
                MatchRule("send", "tool", "equals", "send"),
                MatchRule("receive", "role", "equals", "incoming"),
                receiver_field="to",
                explicit_id_field="message_id",
            ),
        ),
    )
    rows = [
        dict(
            conversation_id="A",
            position=1,
            author="user",
            role="user",
            sent_at="2026-01-05T09:00Z",
            text="Synthetic request",
        ),
        dict(
            conversation_id="A",
            position=2,
            author="A",
            tool="send",
            to="B",
            message_id="m1",
            sent_at="2026-01-05T09:01Z",
        ),
        dict(
            conversation_id="B",
            position=1,
            author="A",
            role="incoming",
            message_id="m1",
            sent_at="2026-01-05T09:01Z",
        ),
    ]
    imported = import_chat_log(rows, mapping)
    if not imported.valid:
        raise RuntimeError(imported.import_issues)
    traces = reconstruct_traces(
        imported.candidate,
        TraceSpec("message", tie_policy="concurrent", time_precision=minute),
    )
    constraints = evaluate_constraints(
        traces,
        ConstraintSpec(
            (
                TimedResponseRule(
                    "ack_10m", "sent", "received", 0, 600_000_000, "first"
                ),
            ),
            "closed",
        ),
    )
    handover = discover_handover(
        imported.candidate, HandoverSpec(time_precision=minute)
    )
    temporal = measure_temporal(
        imported.candidate,
        TemporalSpec("message", tie_policy="concurrent", time_precision=minute),
    )
    output.mkdir(parents=True, exist_ok=True)
    for name, result in (
        ("traces", traces),
        ("constraints", constraints),
        ("handover", handover),
        ("temporal", temporal),
    ):
        write_result(result, output / (name + ".json"))
    return {
        "mapping_digest": imported.mapping_digest,
        "turns": imported.turn_count,
        "links": len(handover.value.links),
        "indeterminate": constraints.value.rules[0].indeterminate_count,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))
