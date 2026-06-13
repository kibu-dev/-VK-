import threading
from database import init_db
from publisher import run_publisher
from messenger import run_messenger

if __name__ == "__main__":
    init_db()
    print("✅ База данных готова")
    
    # Создаём файл со словами, если его нет
    import os
    from config import FORBIDDEN_WORDS_FILE
    from utils import save_forbidden_words
    if not os.path.exists(FORBIDDEN_WORDS_FILE):
        save_forbidden_words(["реклама", "раскрутка", "накрутка", "магазин", "скидка", "заработок", "биткоин", "крипта", "услуги"])
    
    threading.Thread(target=run_publisher, daemon=True).start()
    run_messenger()
