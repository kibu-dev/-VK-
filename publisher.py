import time
import traceback
import vk_api
from config import *
from utils import *
from database import add_post

def publish_post_from_suggestion(vk_user, post_id, uid, text):
    is_anon = contains_anonymous(text)
    
    if is_anon:
        final_text = f"{text}\n\nАвтор: Аноним"
    else:
        try:
            user_info = vk_user.users.get(user_ids=uid, fields="first_name,last_name")[0]
            author_link = f"[id{uid}|{user_info['first_name']} {user_info['last_name']}]"
            final_text = f"{text}\n\nАвтор: {author_link}"
        except:
            final_text = f"{text}\n\nАвтор: Пользователь"
    
    attachments = []
    try:
        response = vk_user.wall.get(owner_id=-GROUP_ID, filter="suggests", count=100)
        for p in response.get("items", []):
            if p["id"] == post_id:
                attachments = build_attachments(p)
                break
    except:
        pass
    
    result = vk_user.wall.post(
        owner_id=-GROUP_ID,
        message=final_text,
        attachments=attachments,
        from_group=1
    )
    vk_user.wall.delete(owner_id=-GROUP_ID, post_id=post_id)
    return result["post_id"]

def run_publisher():
    vk = vk_api.VkApi(token=USER_TOKEN).get_api()
    published = load_published()
    last_publish_time = None

    print("🚀 Публикатор запущен")
    print(f"⏱ Интервал между публикациями: {PUBLISH_INTERVAL // 60} мин.")

    while True:
        try:
            items = vk.wall.get(owner_id=-GROUP_ID, filter="suggests", count=100)["items"]
            pending = [p for p in items if p["id"] not in published["published"]]
            
            print(f"\n📨 Найдено предложенных постов: {len(items)}")
            print(f"⏳ Ожидают публикации: {len(pending)}")
            
            for post in pending:
                pid = post["id"]
                uid = post.get("from_id")
                text = post.get("text", "")
                
                # Спам-слова
                if is_spam(text):
                    moderation = load_moderation()
                    if pid not in moderation["sent"]:
                        if ADMIN_ID:
                            try:
                                user_info = vk.users.get(user_ids=uid, fields="first_name,last_name")[0]
                                user_name = f"{user_info['first_name']} {user_info['last_name']}"
                            except:
                                user_name = "Неизвестный"
                            admin_msg = f"🚨 ПОДОЗРИТЕЛЬНЫЙ ПОСТ (запрещённые слова)\n\nАвтор: {user_name}\n\nТекст:\n{text}\n\nID поста: {pid}"
                            vk_group = vk_api.VkApi(token=GROUP_TOKEN, api_version='5.131').get_api()
                            vk_group.messages.send(user_id=ADMIN_ID, message=admin_msg, random_id=0, group_id=GROUP_ID)
                            moderation["sent"].append(pid)
                            save_moderation(moderation)
                    continue
                
                # Ссылки
                if contains_any_link(text):
                    moderation = load_moderation()
                    if pid not in moderation["sent"]:
                        if ADMIN_ID:
                            try:
                                user_info = vk.users.get(user_ids=uid, fields="first_name,last_name")[0]
                                user_name = f"{user_info['first_name']} {user_info['last_name']}"
                            except:
                                user_name = "Неизвестный"
                            is_anon = contains_anonymous(text)
                            author_text = f"Автор: {user_name}" if not is_anon else "Автор: Аноним"
                            post_link = f"https://vk.com/wall-{GROUP_ID}_{pid}?w=wall-{GROUP_ID}_{pid}"
                            admin_msg = f"🚨 ПОДОЗРИТЕЛЬНЫЙ ПОСТ (ссылки)\n\n{author_text}\n\nТекст:\n{text}\n\nID поста: {pid}\n\n{post_link}"
                            vk_group = vk_api.VkApi(token=GROUP_TOKEN, api_version='5.131').get_api()
                            vk_group.messages.send(user_id=ADMIN_ID, message=admin_msg, random_id=0, group_id=GROUP_ID)
                            moderation["sent"].append(pid)
                            save_moderation(moderation)
                    continue
                
                # Интервал между постами
                if last_publish_time and (time.time() - last_publish_time) < PUBLISH_INTERVAL:
                    continue
                
                # Публикуем обычный пост
                anonymous = contains_anonymous(text)
                if anonymous:
                    final = f"{text}\n\nАвтор: Аноним"
                else:
                    first, last = get_user_name(vk, uid)
                    author_link = f"[id{uid}|{first} {last}]"
                    final = f"{text}\n\nАвтор: {author_link}"
                
                attachments = build_attachments(post)
                result = vk.wall.post(owner_id=-GROUP_ID, message=final, attachments=attachments, from_group=1)
                
                vk.wall.delete(owner_id=-GROUP_ID, post_id=pid)
                published["published"].append(result["post_id"])
                save_published(published)
                add_post(uid, result["post_id"], text)
                last_publish_time = time.time()
                print(f"✅ Пост {pid} опубликован")
            
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Ошибка публикатора: {e}")
            traceback.print_exc()
            time.sleep(60)
