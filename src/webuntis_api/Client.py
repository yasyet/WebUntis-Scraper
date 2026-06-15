import requests
import re
import sys

class Client:
    endpoints = {
        "j_spring_security_check": "j_spring_security_check",
        "create_bearer_token": "api/token/new",
    }

    def __init__(self, username: str, password: str, school: str):
        if not username.strip():
            raise ValueError("Missing Username.")
        if not password.strip():
            raise ValueError("Missing Password.")
        if not school.strip():
            raise ValueError("Missing School.")
        
        self.last_error = None

        self.username = username.strip()
        self.password = password.strip()
        self.school = school.strip()

        self.server = f"{school}.webuntis.com"
        self.base_url = f"https://{self.server}/WebUntis/"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        })

        response = self.session.get(self.base_url)
        response.raise_for_status()

        self.x_crsf_token = self._get_x_csrf_token(response.text)
        self.session.headers.update({
            "x-csrf-token": self.x_crsf_token
        })

        self.bearer_token = self.login()

    def _get_x_csrf_token(self, html: str) -> str:
        """
        Returns the X-Crsf-Token
        """
        match = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', html)
        if not match:
            raise ValueError("csrfToken not found in WebUntis response HTML")

        return match.group(1)
    
    def login(self) -> str:
        """
        """
        security_check_url = self.base_url + self.endpoints["j_spring_security_check"]
        security_check_response: requests.Response = self.session.post(url=security_check_url, data={
            "j_username": self.username,
            "j_password": self.password,
            "school": self.school,
            "token": "",
        })

        if security_check_response.url.split(sep="/")[-1] != "index.do":
            self.last_error = "Wrong Username or Password."
            print(f"Error: {self.last_error} Exiting...")

            self.session.close()
            sys.exit(0)

        create_bearer_token_url = self.base_url + self.endpoints["create_bearer_token"]
        create_bearer_token_response = self.session.get(url=create_bearer_token_url)
        
        return "Bearer " + create_bearer_token_response.text
