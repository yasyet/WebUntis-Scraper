from datetime import datetime
from typing import Any

from webuntis_api.webuntis_api import Period


def _candidate_score(period: Period) -> int:
    score = 0
    if period.layout_group is not None:
        score += 1
    if period.status in {"ADDITIONAL", "CHANGED"}:
        score += 2
    if period.type == "ADDITIONAL_PERIOD":
        score += 2
    if period.substitution_text:
        score += 2
    if period.subject_name.lower() == "vertretung":
        score += 2
    return score


def _resolve_substitutions(periods: list[Period]) -> None:
    for cancelled_period in periods:
        if not cancelled_period.cancelled:
            continue

        candidates = [
            period
            for period in periods
            if period is not cancelled_period
            and period.start == cancelled_period.start
            and period.end == cancelled_period.end
            and not period.cancelled
        ]

        if cancelled_period.layout_group is not None:
            same_group_candidates = [
                period
                for period in candidates
                if period.layout_group == cancelled_period.layout_group
            ]
            if same_group_candidates:
                candidates = same_group_candidates

        if not candidates:
            cancelled_period.substituted = False
            cancelled_period.substitution_period = None
            continue

        substitution_period = max(candidates, key=_candidate_score)
        if _candidate_score(substitution_period) > 0:
            cancelled_period.substituted = True
            cancelled_period.substitution_period = substitution_period
        else:
            cancelled_period.substituted = False
            cancelled_period.substitution_period = None


def parse_timetable_to_lesson(
    timetable: dict[str, Any], client: Any | None = None
) -> list[Period]:
    """Function parses a timetable json into a list of all periods."""
    if not timetable:
        raise TypeError("Function requires valid timetable")

    days: list[dict[str, Any]] = timetable["days"]
    if not days:
        raise ValueError('Timetable does not contains "days"')

    periods: list[Period] = []

    for day in days:
        entries = day.get("gridEntries", [])

        for entry in entries:
            duration = entry["duration"]
            start = datetime.fromisoformat(duration["start"])
            end = datetime.fromisoformat(duration["end"])

            period = Period(
                start=start,
                end=end,
                type=entry["type"],
                status=entry["status"],
                teacher=entry["position1"][0]["current"]["longName"],
                subject=entry["position2"][0]["current"]["longName"],
                room=entry["position3"][0]["current"]["shortName"],
                layout_group=entry.get("layoutGroup"),
                substitution_text=entry.get("substitutionText"),
                client=client,
            )
            periods.append(period)

    _resolve_substitutions(periods)
    return periods
