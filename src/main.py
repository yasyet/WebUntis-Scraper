from webuntis_api.webuntis_api import Client
from webuntis_api.util import get_taught_periods, get_cancellations
from datetime import datetime
import config


def main():
    client = Client(
        username=config.USERNAME, password=config.PASSWORD, school=config.SCHOOL
    )
    client.login()

    start = datetime(2026, 6, 16)
    end = datetime(2026, 6, 16)
    periods = client.get_timetable(start=start, end=end)

    print("Taught lessons:")
    for period in get_taught_periods(periods):
        print(f"  {period}")

    print("\nCancellations:")
    for period in get_cancellations(periods):
        if period.substituted:
            print(f"  {period} → substituted by {period.substitution_period}")
        else:
            print(f"  {period} (no substitution)")


if __name__ == "__main__":
    main()
