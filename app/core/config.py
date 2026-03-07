import os
from dotenv import load_dotenv

load_dotenv()

RESERVED_WORDS = {"delete", "login", "signup", "shorten", "stats", "admin", "api", "docs", "users"}

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
DOMAIN = os.getenv("DOMAIN")
DATABASE_URL = os.getenv("DATABASE_URL")