from datetime import datetime
from typing import Any

from webuntis_api.webuntis_api import Period


def _resolve_cancelled_periods(periods: list[Period]):
    return [period for period in periods if not period.cancelled]


def _resolve_substitutions(_periods: list[Period]):
    periods = _periods.copy()

    additional_periods = [
        period for period in periods if period.type == "ADDITIONAL_PERIOD"
    ]

    for period in periods:
        if not period.cancelled:
            continue

        for additional_period in additional_periods:
            if (
                period.start == additional_period.start
                and period.end == additional_period.end
            ):
                periods.remove(period)

    return periods


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
                id=entry["ids"][0],
                start=start,
                end=end,
                type=entry["type"],
                status=entry["status"],
                teacher=entry["position1"][0]["current"]["longName"],
                subject=entry["position2"][0]["current"]["longName"],
                room=entry["position3"][0]["current"]["shortName"],
                client=client,
            )
            periods.append(period)

    return _resolve_cancelled_periods(_resolve_substitutions(periods))
