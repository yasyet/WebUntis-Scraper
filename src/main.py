from webuntis_api.webuntis_api import Client
from webuntis_api.util import parse_timetable_to_lesson
from datetime import datetime
from typing import Any
import config
import json

def main():
    USERNAME = config.USERNAME
    PASSWORD = config.PASSWORD
    SCHOOL = config.SCHOOL

    # Create client to login to WebUntis Servers
    client = Client(username=USERNAME, password=PASSWORD, school=SCHOOL)
    client.login()

    # Create timetable with WebUntis API Client
    start = datetime(2026, 6, 15)
    end = datetime(2026, 6, 19)
    timetable = client.get_timetable(start=start, end=end)
    timetable_json = timetable.json()

    # Parse timetable JSON into Period objects
    periods: list[dict[str, Any]] = parse_timetable_to_lesson(timetable_json)

    for period in periods:
        print(str(period) + "\n")

    # periods = parse_timetable_to_lesson(timetable_json)
    with open("timetable.json", "w", encoding="utf-8") as file:
        json.dump(timetable_json, file, indent=4)

if __name__ == "__main__":
    main()

