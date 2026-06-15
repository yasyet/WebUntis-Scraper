import requests
import re
import sys


class WebUntisError(Exception):
    """Main class for all WebUntis errors."""


class WebUntisNetworkError(WebUntisError):
    """Class for all WebUntis networking erros."""


class WebUntisAuthenticationError(WebUntisError):
    """Class for all authentication related Errors"""


class Client:
    ENDPOINTS = {
        "j_spring_security_check": "j_spring_security_check",
        "create_bearer_token": "api/token/new",
    }

    DEFAULT_TIMEOUT = 15 # 15 Seconds

    def __init__(self, username: str, password: str, school: str, timeout=DEFAULT_TIMEOUT):
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

        # Creating server and url from schoolname
        self.server = f"{school}.webuntis.com"
        self.base_url = f"https://{self.server}/WebUntis/"

        # Logging
        self.last_error: str | None = None

        # Bearer token for authentication
        self.bearer_token: str | None = None

    def _get_x_csrf_token(self, html: str) -> str:
        """
        AI created function to search extract string value from html document.
        """
        match = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', html)
        if not match:
            raise ValueError("csrfToken not found in WebUntis response HTML. Please validate your credentials again (Username, Password, School)")

        return match.group(1)
    
    def login(self) -> str:
        """
        Login function to establish connection to api.
        """
        # Creating requests Session to store cookies
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        response = self.session.get(self.base_url, timeout=self.timeout)
        response.raise_for_status()

        # Grab session-related _csrf token.
        self.x_csrf_token = self._get_x_csrf_token(response.text)
        self.session.headers.update({
            "x-csrf-token": self.x_csrf_token
        })

        # Do j_spring_security_check
        security_check_url = self.base_url + self.ENDPOINTS["j_spring_security_check"]
        security_check_response: requests.Response = self.session.post(url=security_check_url, data={
            "j_username": self.username,
            "j_password": self.password,
            "school": self.school,
            "token": "",
        },
        timeout=self.timeout)

        # Validate security check
        if security_check_response.url.split(sep="/")[-1] != "index.do":
            raise WebUntisAuthenticationError("Error connecting to WebUntis API. Please validate your credentials again (Username, Password, School)")

        # Grab bearer token
        create_bearer_token_url = self.base_url + self.ENDPOINTS["create_bearer_token"]
        create_bearer_token_response = self.session.get(url=create_bearer_token_url, timeout=self.timeout)
        
        # Check if Bearer Token or failed html response got fetched
        if create_bearer_token_response.text[0:1] == "ey":
            raise WebUntisAuthenticationError("Error while grabbing Bearer Token.")
        
        self.bearer_token = "Bearer " + create_bearer_token_response.text
