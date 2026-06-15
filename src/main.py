from webuntis_api.Client import Client as UntisClient
import config

def main():
    USERNAME = config.USERNAME
    PASSWORD = config.PASSWORD
    SCHOOL = config.SCHOOL

    # Create client to communicate to WebUntis Servers
    client = UntisClient(username=USERNAME, password=PASSWORD, school=SCHOOL)
    print(client.bearer_token)

if __name__ == "__main__":
    main()