from webuntis_api.client import Client as UntisClient
from datetime import datetime
import config
import json

def main():
    USERNAME = config.USERNAME
    PASSWORD = config.PASSWORD
    SCHOOL = config.SCHOOL

    # Create client to login to WebUntis Servers
    client = UntisClient(username=USERNAME, password=PASSWORD, school=SCHOOL)
    client.login()

    start = datetime(2026, 6, 15)
    end = datetime(2026, 6, 15)
    timetable = client.get_timetable(start=start, end=end)
    timetable_json = timetable.json()

    with open("timetable.json", "w", encoding="utf-8") as file:
        json.dump(timetable_json, file, indent=4)

if __name__ == "__main__":
    main()

