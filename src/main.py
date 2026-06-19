from webuntis_api.webuntis_api import Client
from datetime import datetime
import config

client: Client | None = None


def main():
    global client

    USERNAME = config.USERNAME
    PASSWORD = config.PASSWORD
    SCHOOL = config.SCHOOL

    # Create client to login to WebUntis Servers
    client = Client(username=USERNAME, password=PASSWORD, school=SCHOOL)
    client.login()

    # Create timetable with WebUntis API Client
    start = datetime(2026, 6, 16)
    end = datetime(2026, 6, 16)
    periods = client.get_timetable(start=start, end=end)

    for period in periods:
        print(period)


if __name__ == "__main__":
    main()
