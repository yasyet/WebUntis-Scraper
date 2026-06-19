from datetime import datetime
from typing import Any
import requests
import re


class WebUntisError(Exception):
    """Base class for all WebUntis errors."""


class WebUntisNetworkError(WebUntisError):
    """Raised on network-level failures talking to WebUntis."""


class WebUntisAuthenticationError(WebUntisError):
    """Raised when login or token retrieval fails."""


class PeriodRegistrationException(Exception):
    """Raised if a Period is constructed with missing required data."""


class Period:
    """Represents a single lesson/period in a timetable."""

    def __init__(
        self,
        id: str,
        start: datetime,
        end: datetime,
        type: str,
        status: str,
        teacher: str,
        subject: str,
        room: str,
        client: "Client | None" = None,
    ):
        missing = [
            name
            for name, value in {
                "id": id,
                "start": start,
                "end": end,
                "type": type,
                "status": status,
                "teacher": teacher,
                "subject": subject,
                "room": room,
            }.items()
            if not value
        ]

        if missing:
            raise PeriodRegistrationException(
                f"Missing period credentials: {', '.join(missing)}"
            )

        self.id = id
        self.start = start
        self.end = end
        self.type = type
        self.status = status
        self.teacher = teacher
        self.subject = subject
        self.room = room
        self.client = client

        self.subject_name = subject.title()
        self.cancelled = self.status == "CANCELLED"

        # Filled in later by _link_substitutions(), once every period of the
        # day already exists as an object — see parse_timetable_to_lesson().
        self.substituted: bool | None = None
        self.substitution_period: "Period | None" = None

    def __str__(self):
        return f"{self.subject_name} mit {self.teacher} in {self.room}"


def _link_substitutions(periods: list[Period]) -> None:
    """
    Second pass over a single day's periods: for every CANCELLED period,
    find the ADDITIONAL_PERIOD occupying the same start/end slot and attach
    it. Runs after every Period object for the day already exists, so this
    is a pure lookup — no recursive construction involved.
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


def parse_timetable_to_lesson(
    timetable: dict[str, Any], client: "Client | None" = None
) -> list[Period]:
    """
    Parses a raw WebUntis timetable JSON into a list of ALL Period objects
    (taught + cancelled), fully linked. Nothing is filtered out here — use
    get_taught_periods() / get_cancellations() for that afterwards.
    """
    if not timetable:
        raise TypeError("Function requires valid timetable")

    days: list[dict[str, Any]] = timetable["days"]
    if not days:
        raise ValueError('Timetable does not contain "days"')

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

        _link_substitutions(day_periods)  # only link within the same day
        periods.extend(day_periods)

    return periods


def get_taught_periods(periods: list[Period]) -> list[Period]:
    """Normal lessons + substitute lessons — what's actually happening."""
    return [period for period in periods if not period.cancelled]


def get_cancellations(periods: list[Period]) -> list[Period]:
    """Every CANCELLED period, substituted or not."""
    return [period for period in periods if period.cancelled]


class Client:
    ENDPOINTS = {
        "login": "WebUntis",
        "j_spring_security_check": "WebUntis/j_spring_security_check",
        "bearer_token": "WebUntis/api/token/new",
        "timetable": "WebUntis/api/rest/view/v1/timetable/entries",
    }

    DEFAULT_TIMEOUT = 15  # seconds

    def __init__(
        self, username: str, password: str, school: str, timeout: int = DEFAULT_TIMEOUT
    ):
        if not username:
            raise ValueError("Missing Username.")
        if not password:
            raise ValueError("Missing Password.")
        if not school:
            raise ValueError("Missing School.")

        self.username = username.strip()
        self.password = password.strip()
        self.school = school.strip()
        self.timeout = timeout

        self.server = f"{school}.webuntis.com"
        self.base_url = f"https://{self.server}/"

        self.last_error: str | None = None
        self.bearer_token: str | None = None
        self.session: requests.Session | None = None

    def _get_x_csrf_token(self, html: str) -> str:
        """Extracts the CSRF token embedded in the WebUntis login page HTML."""
        match = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', html)
        if not match:
            raise ValueError(
                "csrfToken not found in WebUntis response HTML. "
                "Please validate your credentials again (Username, Password, School)"
            )
        return match.group(1)

    def login(self) -> None:
        """
        Full login flow:
          1. GET the login page -> grab CSRF token + initial session cookie
          2. POST credentials to j_spring_security_check -> sets auth cookies
          3. GET /api/token/new again -> now returns the Bearer JWT
        """
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )

        # Step 1: CSRF token + initial cookies
        url = self.base_url + self.ENDPOINTS["login"]
        response = self.session.get(url=url, timeout=self.timeout)
        response.raise_for_status()

        self.x_csrf_token = self._get_x_csrf_token(response.text)
        self.session.headers.update({"x-csrf-token": self.x_csrf_token})

        # Step 2: actual login
        security_check_url = self.base_url + self.ENDPOINTS["j_spring_security_check"]
        security_check_response = self.session.post(
            url=security_check_url,
            data={
                "j_username": self.username,
                "j_password": self.password,
                "school": self.school,
                "token": "",
            },
            timeout=self.timeout,
        )

        if security_check_response.url.split(sep="/")[-1] != "index.do":
            raise WebUntisAuthenticationError(
                "Error connecting to WebUntis API. Please validate your credentials "
                "again (Username, Password, School)"
            )

        # Step 3: Bearer token
        create_bearer_token_url = self.base_url + self.ENDPOINTS["bearer_token"]
        create_bearer_token_response = self.session.get(
            url=create_bearer_token_url, timeout=self.timeout
        )
        create_bearer_token_response.raise_for_status()

        # A valid JWT always starts with "ey" (base64 of '{"'). If it doesn't,
        # something went wrong — e.g. an HTML error page came back instead.
        if not create_bearer_token_response.text.startswith("ey"):
            raise WebUntisAuthenticationError("Error while grabbing Bearer Token.")

        self.bearer_token = "Bearer " + create_bearer_token_response.text
        self.session.headers.update({"Authorization": self.bearer_token})

    def get_timetable(
        self,
        start: datetime,
        end: datetime,
        format: int = 4,
        resource_types: str = "STUDENT",
        resources: int = 474,
        period_types: str = "",
        timetable_type: str = "MY_TIMETABLE",
        layout: str = "START_TIME",
    ) -> list[Period]:
        """Fetches and parses timetable data for the given date range."""
        url = self.base_url + self.ENDPOINTS["timetable"]
        response = self.session.get(
            url=url,
            params={
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "format": format,
                "resourceType": resource_types,
                "resources": resources,
                "periodTypes": period_types,
                "timetableType": timetable_type,
                "layout": layout,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        return parse_timetable_to_lesson(response.json(), client=self)
