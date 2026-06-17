from webuntis_api.webuntis_api import Period
from datetime import datetime
from typing import Any
import json


def parse_timetable_to_lesson(timetable: dict[str, Any]) -> list[Period]:
    """Function parses a timetable json into a list of all periods."""
    if not timetable:
        raise TypeError("Function requires valid timetable")

    # Indexing "days" which contains all the days with their periods
    days: list[dict[str, Any]] = timetable["days"]
    if not days:
        raise ValueError('Timetable does not contains "days"')

    periods = []
    # Iterate over each day in given timetable
    for day in days:
        entries = day.get("gridEntries", [])

        # Iterate over each period in given day
        for entry in entries:
            # Index start and end of period
            duration = entry["duration"]
            start = datetime.fromisoformat(duration["start"])
            end = datetime.fromisoformat(duration["end"])

            # Index type and status of period
            type = entry["type"]
            status = entry["status"]

            # Index teacher
            teacher = entry["position1"][0]["current"]["longName"]

            # Index subject
            subject = entry["position2"][0]["current"]["longName"]

            # Index room
            room = entry["position3"][0]["current"]["shortName"]

            # Create Period object
            period = Period(
                start=start,
                end=end,
                type=type,
                status=status,
                teacher=teacher,
                subject=subject,
                room=room,
            )
            periods.append(period)

    # Return list object of Period
    return periods
