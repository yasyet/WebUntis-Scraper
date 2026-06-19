from datetime import datetime
from typing import Any

from webuntis_api.webuntis_api import Period


def _link_substitutions(periods: list[Period]) -> None:
    """
    Second pass: for every CANCELLED period, look for a matching ADDITIONAL_PERIOD
    (same start/end) and attach it. Mutates in place — nothing is removed or created.
    """
    additional_periods = [p for p in periods if p.type == "ADDITIONAL_PERIOD"]

    for period in periods:
        if not period.cancelled:
            continue

        substitute = next(
            (
                additional
                for additional in additional_periods
                if additional.start == period.start and additional.end == period.end
            ),
            None,
        )

        period.substitution_period = substitute
        period.substituted = substitute is not None


def get_taught_periods(periods: list[Period]) -> list[Period]:
    """Normal lessons + substitute lessons — what's actually happening."""
    return [period for period in periods if not period.cancelled]


def get_cancellations(periods: list[Period]) -> list[Period]:
    """Every CANCELLED period, substituted or not — this is what the notifier needs."""
    return [period for period in periods if period.cancelled]


def parse_timetable_to_lesson(
    timetable: dict[str, Any], client: Any | None = None
) -> list[Period]:
    """Parses a timetable json into ALL periods (cancelled + taught), fully linked."""
    if not timetable:
        raise TypeError("Function requires valid timetable")

    days: list[dict[str, Any]] = timetable["days"]
    if not days:
        raise ValueError('Timetable does not contains "days"')

    periods: list[Period] = []

    for day in days:
        entries = day.get("gridEntries", [])
        day_periods: list[Period] = []

        for entry in entries:
            duration = entry["duration"]
            start = datetime.fromisoformat(duration["start"])
            end = datetime.fromisoformat(duration["end"])

            day_periods.append(
                Period(
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
            )

        _link_substitutions(day_periods)  # linking only makes sense within the same day
        periods.extend(day_periods)

    return periods
