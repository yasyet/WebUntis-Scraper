from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv("SCHOOL_USERNAME")
PASSWORD = os.getenv("SCHOOL_PASSWORD")
SCHOOL = os.getenv("SCHOOL")