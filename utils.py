import re
import json
from config import (
    FORBIDDEN_WORDS_FILE, PUBLISHED_FILE, MODERATION_FILE
)

# Функции работы с JSON
def load_json_file(filepath, default=None):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def save_json_file(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_forbidden_words():
    data = load_json_file(FORBIDDEN_WORDS_FILE, {"words": []})
    return data.get("words", [])

def save_forbidden_words(words):
    save_json_file(FORBIDDEN_WORDS_FILE, {"words": words})

def load_published():
    return load_json_file(PUBLISHED_FILE, {"published": []})

def save_published(data):
    save_json_file(PUBLISHED_FILE, data)

def load_moderation():
    return load_json_file(MODERATION_FILE, {"sent": []})

def save_moderation(data):
    save_json_file(MODERATION_FILE, data)

# Проверка на спам
def is_spam(text):
    if not text:
        return False
    forbidden_words = load_forbidden_words()
    text_lower = text.lower()
    for word in forbidden_words:
        if word in text_lower:
            return True
    return False

# Проверка на ссылки
def contains_any_link(text):
    if not text:
        return False
    patterns = [
        r'https?://[^\s]+',
        r'www\.[^\s]+',
        r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*'
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

# Анонимность
def contains_anonymous(text):
    keywords = ["анон", "анонимно", "аноним", "#анон", "#анонимно", "#аноним"]
    for kw in keywords:
        if kw in text.lower():
            return True
    return False

def build_attachments(post):
    attachments = []
    for a in post.get("attachments", []):
        t = a["type"]
        obj = a[t]
        owner_id = obj.get("owner_id")
        item_id = obj.get("id")
        access_key = obj.get("access_key", "")
        if owner_id and item_id:
            attachment = f"{t}{owner_id}_{item_id}"
            if access_key:
                attachment += f"_{access_key}"
            attachments.append(attachment)
    return ",".join(attachments) if attachments else None

def get_user_name(vk, user_id):
    try:
        user = vk.users.get(user_ids=user_id, fields="first_name,last_name")[0]
        return user["first_name"], user["last_name"]
    except Exception:
        return "Пользователь", ""
