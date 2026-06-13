import os
from dotenv import load_dotenv

load_dotenv()

# Токены
USER_TOKEN = os.getenv("USER_TOKEN")
GROUP_TOKEN = os.getenv("GROUP_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Настройки
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
PUBLISH_INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "600"))

# Файлы
PUBLISHED_FILE = "published.json"
MODERATION_FILE = "moderation.json"
FORBIDDEN_WORDS_FILE = "forbidden_words.json"
DB_PATH = "posts.db"
