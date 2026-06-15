from webuntis_api.client import Client as UntisClient
import config

def main():
    USERNAME = config.USERNAME
    PASSWORD = config.PASSWORD
    SCHOOL = config.SCHOOL

    # Create client to login to WebUntis Servers
    client = UntisClient(username=USERNAME, password=PASSWORD, school=SCHOOL)
    client.login()

if __name__ == "__main__":
    main()