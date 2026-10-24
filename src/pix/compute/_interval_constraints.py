"""Constraint witnesses when source observations do not establish a total order."""

from pix.compute._time import elapsed, micros
from pix.contracts.constraint import (
    ConstraintWitness,
    PrecedenceRule,
    TimedResponseRule,
)


def bounds(event):
    return (
        (event.time_lower, event.time_upper)
        if event.time_lower is not None
        else (event.time, event.time)
    )


def activation_witnesses(rule, trace, closed, concurrent):
    witnesses = []
    precedent = isinstance(rule, PrecedenceRule)
    activator = rule.target if precedent else rule.activity
    response = rule.activity if precedent else rule.target
    for index, activation in enumerate(trace.events):
        if activation.activity != activator:
            continue
        candidates = []
        for j, event in enumerate(trace.events):
            if event.event_id == activation.event_id or event.activity != response:
                continue
            same = concurrent and event.order_group == activation.order_group
            eligible = (j < index if precedent else j > index) or same
            if eligible:
                candidates.append(event)
        if precedent:
            candidates.reverse()
        timed = isinstance(rule, TimedResponseRule)
        if candidates and timed and rule.response_selection == "first":
            first = candidates[0]
            # Every member of the first unordered group can be the first target.
            candidates = [
                e
                for e in candidates
                if concurrent and e.order_group == first.order_group
            ] or [first]
        outcomes = []
        for candidate in candidates:
            lo, hi = (
                elapsed(bounds(candidate), bounds(activation))
                if precedent
                else elapsed(bounds(activation), bounds(candidate))
            )
            unknown = concurrent and candidate.order_group == activation.order_group
            if unknown or lo is None or lo < 0:
                state, reason = (
                    "indeterminate",
                    "response_order_unknown_within_precision",
                )
            elif hi is None:
                state, reason = "indeterminate", "response_time_upper_unobserved"
            elif not timed:
                state, reason = (
                    "fulfilled",
                    "prior_activity_observed"
                    if precedent
                    else "later_response_observed",
                )
            elif rule.min_microseconds <= lo and hi <= rule.max_microseconds:
                state, reason = "fulfilled", "response_within_inclusive_window"
            elif hi < rule.min_microseconds or lo > rule.max_microseconds:
                state, reason = "violated", "response_interval_outside_window"
            else:
                state, reason = (
                    "indeterminate",
                    "response_window_overlaps_precision_interval",
                )
            outcomes.append((state, reason, candidate, lo, hi))
        if outcomes:
            if timed and rule.response_selection == "first":
                states = {o[0] for o in outcomes}
                chosen = outcomes[0]
                if len(states) != 1 or "indeterminate" in states:
                    chosen = (
                        "indeterminate",
                        "response_order_unknown_within_precision",
                        chosen[2],
                        min(o[3] for o in outcomes)
                        if all(o[3] is not None for o in outcomes)
                        else None,
                        max(o[4] for o in outcomes)
                        if all(o[4] is not None for o in outcomes)
                        else None,
                    )
            else:
                chosen = next(
                    (o for o in outcomes if o[0] == "fulfilled"),
                    next((o for o in outcomes if o[0] == "indeterminate"), outcomes[0]),
                )
            state, reason, candidate, lo, hi = chosen
            if timed and rule.response_selection == "first" and len(outcomes) > 1:
                lo = (
                    min(o[3] for o in outcomes)
                    if all(o[3] is not None for o in outcomes)
                    else None
                )
                hi = (
                    max(o[4] for o in outcomes)
                    if all(o[4] is not None for o in outcomes)
                    else None
                )
            # With an open prefix an absent qualifying future target is still possible.
            if (
                state == "violated"
                and not closed
                and timed
                and rule.response_selection == "any"
            ):
                last_lower = bounds(trace.events[-1])[0]
                activation_upper = bounds(activation)[1]
                if (
                    activation_upper is None
                    or micros(last_lower - activation_upper) <= rule.max_microseconds
                ):
                    state, reason = "pending", "response_window_not_closed"
            evidence = (
                (candidate.event_id, activation.event_id)
                if precedent
                else (activation.event_id, candidate.event_id)
            )
            if len(outcomes) > 1 and timed and rule.response_selection == "first":
                evidence = (
                    activation.event_id,
                    *sorted(o[2].event_id for o in outcomes),
                )
        else:
            candidate, lo, hi = None, None, None
            state = "violated" if closed or precedent else "pending"
            reason = (
                "required_prior_activity_absent"
                if precedent
                else "no_response_in_window_at_close"
                if closed
                else "response_window_not_closed"
            )
            if timed and not closed:
                upper = bounds(activation)[1]
                if (
                    upper is not None
                    and micros(bounds(trace.events[-1])[0] - upper)
                    > rule.max_microseconds
                ):
                    state, reason = (
                        "violated",
                        "observed_prefix_passed_response_deadline",
                    )
            evidence = (activation.event_id,)
        witnesses.append(
            ConstraintWitness(
                state,
                activation.event_id,
                evidence,
                None,
                lo if lo is not None and lo == hi else None,
                reason,
                lo,
                hi,
            )
        )
    return tuple(witnesses)
