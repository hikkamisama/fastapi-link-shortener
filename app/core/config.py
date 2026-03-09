import os

from dotenv import load_dotenv

load_dotenv()

RESERVED_WORDS = {
    "admin",
    "api",
    "cleanup",
    "cleanup/inactive",
    "cleanup/purge",
    "delete",
    "docs",
    "history"
    "history/deleted",
    "login",
    "search",
    "signup",
    "shorten",
    "stats",
    "users",
}

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
DOMAIN = os.getenv("DOMAIN")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
