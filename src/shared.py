from dotenv import load_dotenv
import os

load_dotenv()

AUTH_TOKEN = os.getenv("AUTH_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
YADISK_TOKEN = os.getenv("YADISK_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
