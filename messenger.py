import re
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from config import *
from utils import *
from database import get_user_posts, delete_user_post, get_post_author, add_post
from keyboards import *
from publisher import publish_post_from_suggestion

waiting_support = set()
selected_post_for_delete = {}

def run_messenger():
    vk_session = vk_api.VkApi(token=GROUP_TOKEN, api_version="5.131")
    vk = vk_session.get_api()
    vk_user_session = vk_api.VkApi(token=USER_TOKEN, api_version="5.131")
    vk_user = vk_user_session.get_api()
    longpoll = VkLongPoll(vk_session, group_id=GROUP_ID, mode=2, preload_messages=True)

    print("🤖 ЛС бот запущен")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            text = event.text.strip() if event.text else ""
            
            # Админ-команды
            if user_id == ADMIN_ID:
                if text.startswith("!pub "):
                    try:
                        post_id = int(text.split()[1])
                        response = vk_user.wall.get(owner_id=-GROUP_ID, filter="suggests", count=100)
                        post = None
                        for p in response.get("items", []):
                            if p["id"] == post_id:
                                post = p
                                break
                        if post:
                            uid = post.get("from_id")
                            post_text = post.get("text", "")
                            new_post_id = publish_post_from_suggestion(vk_user, post_id, uid, post_text)
                            add_post(uid, new_post_id, post_text)
                            send_message(vk, user_id, f"✅ Пост #{post_id} опубликован!", get_main_keyboard())
                            mod = load_moderation()
                            if post_id in mod["sent"]:
                                mod["sent"].remove(post_id)
                                save_moderation(mod)
                        else:
                            send_message(vk, user_id, f"❌ Пост #{post_id} не найден", get_main_keyboard())
                    except Exception as e:
                        send_message(vk, user_id, f"❌ Ошибка: {e}", get_main_keyboard())
                    continue
                
                elif text.startswith("!del "):
                    try:
                        post_id = int(text.split()[1])
                        vk_user.wall.delete(owner_id=-GROUP_ID, post_id=post_id)
                        send_message(vk, user_id, f"❌ Пост #{post_id} удалён", get_main_keyboard())
                        mod = load_moderation()
                        if post_id in mod["sent"]:
                            mod["sent"].remove(post_id)
                            save_moderation(mod)
                    except Exception as e:
                        send_message(vk, user_id, f"❌ Ошибка: {e}", get_main_keyboard())
                    continue
                
                elif text.startswith("!addw "):
                    try:
                        new_word = text[6:].strip().lower()
                        if new_word:
                            words = load_forbidden_words()
                            if new_word not in words:
                                words.append(new_word)
                                save_forbidden_words(words)
                                send_message(vk, user_id, f"✅ Слово '{new_word}' добавлено", get_main_keyboard())
                            else:
                                send_message(vk, user_id, f"⚠️ Слово '{new_word}' уже в списке", get_main_keyboard())
                        else:
                            send_message(vk, user_id, f"❌ Формат: !addw слово", get_main_keyboard())
                    except:
                        send_message(vk, user_id, f"❌ Ошибка", get_main_keyboard())
                    continue
                
                elif text.startswith("!delw "):
                    try:
                        del_word = text[6:].strip().lower()
                        if del_word:
                            words = load_forbidden_words()
                            if del_word in words:
                                words.remove(del_word)
                                save_forbidden_words(words)
                                send_message(vk, user_id, f"✅ Слово '{del_word}' удалено", get_main_keyboard())
                            else:
                                send_message(vk, user_id, f"⚠️ Слово '{del_word}' не найдено", get_main_keyboard())
                        else:
                            send_message(vk, user_id, f"❌ Формат: !delw слово", get_main_keyboard())
                    except:
                        send_message(vk, user_id, f"❌ Ошибка", get_main_keyboard())
                    continue
                
                elif text == "!listw":
                    words = load_forbidden_words()
                    if words:
                        send_message(vk, user_id, "📋 Запрещённые слова:\n" + ", ".join(words), get_main_keyboard())
                    else:
                        send_message(vk, user_id, "📋 Список запрещённых слов пуст", get_main_keyboard())
                    continue

            # Поддержка
            if user_id in waiting_support:
                if text.lower() in ["🔙 отмена", "/cancel"]:
                    waiting_support.discard(user_id)
                    send_message(vk, user_id, "❌ Отменено.", get_main_keyboard())
                else:
                    waiting_support.discard(user_id)
                    msg_id = event.message_id if hasattr(event, 'message_id') else event.id
                    if ADMIN_ID:
                        try:
                            dialog_link = f"https://vk.com/gim{GROUP_ID}?sel={user_id}"
                            vk.messages.send(user_id=ADMIN_ID, message=f"📨 ОБРАЩЕНИЕ В ПОДДЕРЖКУ\n\n{dialog_link}", random_id=0, forward_messages=msg_id, group_id=GROUP_ID)
                            send_message(vk, user_id, "✅ Сообщение отправлено администратору!", get_main_keyboard())
                        except Exception as e:
                            send_message(vk, user_id, "❌ Ошибка при отправке.", get_main_keyboard())
                continue

            # Обычные команды
            text_lower = text.lower()
            
            if text_lower in ["начать", "меню", "start"]:
                send_message(vk, user_id, f"👋 Добро пожаловать!", get_main_keyboard())

            elif text_lower == "🗑 удалить мой пост":
                posts = get_user_posts(user_id)
                if not posts:
                    send_message(vk, user_id, "📭 У вас нет опубликованных постов.", get_main_keyboard())
                else:
                    send_message(vk, user_id, f"📋 У вас {len(posts)} пост(ов).\nВыберите какой удалить:", get_posts_keyboard(posts))

            elif text_lower == "🆘 написать в поддержку":
                waiting_support.add(user_id)
                send_message(vk, user_id, "📝 Напишите ваше сообщение администратору.\nНажмите «Отмена» чтобы вернуться в меню.", get_cancel_keyboard())

            elif text_lower == "🔙 отмена":
                send_message(vk, user_id, "Главное меню:", get_main_keyboard())

            elif text_lower == "🔙 назад в меню":
                selected_post_for_delete.pop(user_id, None)
                send_message(vk, user_id, "Главное меню:", get_main_keyboard())

            elif text_lower == "❌ нет":
                selected_post_for_delete.pop(user_id, None)
                send_message(vk, user_id, "Удаление отменено.", get_main_keyboard())

            elif text_lower == "✅ да, удалить":
                if user_id in selected_post_for_delete and selected_post_for_delete[user_id]:
                    post_id = selected_post_for_delete[user_id]
                    if get_post_author(post_id) == user_id:
                        try:
                            vk_user.wall.delete(owner_id=-GROUP_ID, post_id=post_id)
                            delete_user_post(user_id, post_id)
                            send_message(vk, user_id, f"✅ Пост #{post_id} удален!", get_main_keyboard())
                            selected_post_for_delete.pop(user_id, None)
                        except Exception as e:
                            send_message(vk, user_id, f"❌ Ошибка: {e}", get_main_keyboard())
                    else:
                        send_message(vk, user_id, "❌ Это не ваш пост!", get_main_keyboard())
                else:
                    send_message(vk, user_id, "Сначала выберите пост.", get_main_keyboard())

            elif text_lower.startswith("🗑 ") and text_lower != "🗑 удалить мой пост":
                try:
                    match = re.search(r"🗑 (\d+)\.", text)
                    if match:
                        idx = int(match.group(1)) - 1
                        posts = get_user_posts(user_id)
                        if 0 <= idx < len(posts):
                            post_id = posts[idx]['post_id']
                            selected_post_for_delete[user_id] = post_id
                            send_message(vk, user_id, f"⚠️ Удалить пост #{post_id}?", get_confirm_keyboard())
                        else:
                            send_message(vk, user_id, "❌ Пост не найден", get_main_keyboard())
                    else:
                        send_message(vk, user_id, "❌ Ошибка", get_main_keyboard())
                except Exception as e:
                    send_message(vk, user_id, f"❌ Ошибка: {e}", get_main_keyboard())
                continue

            else:
                send_message(vk, user_id, "Нажмите на кнопку в меню", get_main_keyboard())

def send_message(vk, user_id, text, keyboard=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=0,
            keyboard=keyboard.get_keyboard() if keyboard else None,
        )
    except Exception as e:
        print(f"Ошибка отправки: {e}")
