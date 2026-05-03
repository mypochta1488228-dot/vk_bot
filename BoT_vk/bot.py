import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import time
import threading
import json
from flask import Flask  # ✅ Добавляем Flask

# ================================
# НАСТРОЙКИ
# ================================
TOKEN = 'vk1.a.DbVRsdCShYj5rCNpjbvRZk_1VJcu8FyQv7i-8yQT8GPxTVSxjCPeBxsEyHmMRjLSqP7ZPvTANQqSGm92l9NFR2yXdLJUj42ihZGgOUiblEZ-hJ9_I8jzHfSXdF7F7c_rVHW0Tw2x0fSLkg016PLN6-EHQMw99alH1ujxzTgG5vYGfj0e6CRSkm3D_zijv0MmtcXdfMdoCdTBjNUo-0YgTg'
GROUP_ID = 238283135

LIST_1 = {
    10:  'аааааааааа',
    25:  'бббббббббб',
    37:  'вввввввввв',
    42:  'гггггггггг',
    58:  'дддддддддд'
}

LIST_2 = {
    63:  'ееееееееее',
    71:  'жжжжжжжжжж',
    84:  'зззззззззз',
    95:  'ииииииииии',
    100: 'кккккккккк'
}

# ================================
# ✅ FLASK ДЛЯ ПИНГОВ
# ================================
app = Flask(__name__)

@app.route('/')
def hello():
    """Главная страница - показывает что бот работает"""
    return '🤖 Бот работает! Последний пинг: ' + time.strftime('%H:%M:%S')

@app.route('/ping')
def ping():
    """Эндпоинт для пингов от GitHub Actions"""
    return 'OK', 200

@app.route('/health')
def health():
    """Проверка здоровья бота"""
    return {'status': 'alive', 'time': time.strftime('%H:%M:%S')}, 200

# Запуск Flask в отдельном потоке
def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Запускаем Flask при старте бота
threading.Thread(target=run_flask, daemon=True).start()
print("🌐 Flask запущен на порту 8080")
print("🔍 URL для пинга: https://ТВОЙ_БОТ.onrender.com/ping")

# ================================
# Подключение к VK
# ================================
print("🔍 Подключение к VK API...")
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)
print("✅ Бот запущен!\n")

user_data = {}

# ================================
# Создание клавиатуры
# ================================
def create_keyboard(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'blocked': False, 
            'chosen_list1': [],
            'chosen_list2': [],
            'current_list': 1
        }
    
    data = user_data[user_id]
    current_list = data['current_list']
    
    if current_list == 1:
        all_nums = LIST_1
        chosen = data['chosen_list1']
    else:
        all_nums = LIST_2
        chosen = data['chosen_list2']
    
    available = [n for n in all_nums.keys() if n not in chosen]
    
    if not available:
        if current_list == 1:
            data['current_list'] = 2
            return create_keyboard(user_id)
        else:
            data['current_list'] = 1
            return create_keyboard(user_id)
    
    buttons = []
    row = []
    
    for num in available:
        button = {
            "action": {
                "type": "callback",
                "label": f"🎲 {num}",
                "payload": json.dumps({"num": num})
            },
            "color": "primary"
        }
        row.append(button)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    return json.dumps({
        "one_time": False,
        "inline": True,
        "buttons": buttons
    })

# ================================
# Таймер (100 секунд)
# ================================
def start_timer(user_id):
    time.sleep(100)
    user_data[user_id]['blocked'] = False
    
    data = user_data[user_id]
    
    list1_remaining = len(LIST_1) - len(data['chosen_list1'])
    list2_remaining = len(LIST_2) - len(data['chosen_list2'])
    
    if list1_remaining == 0 and list2_remaining == 0:
        vk.messages.send(
            user_id=user_id,
            from_group=1,
            message="🎉 **Поздравляю!**\n\nТы выбрал все числа!\n\nНачни заново командой /start",
            random_id=random.randint(1, 1000000)
        )
        print(f"🎉 Пользователь {user_id} завершил игру!")
        return
    
    keyboard = create_keyboard(user_id)
    if keyboard:
        vk.messages.send(
            user_id=user_id,
            from_group=1,
            message="Можно выбирать снова:",
            keyboard=keyboard,
            random_id=random.randint(1, 1000000)
        )
        print(f"⏳ Таймер завершён для пользователя {user_id}")

# ================================
# Основной цикл
# ================================
for event in longpoll.listen():
    try:
        if event.type == VkBotEventType.MESSAGE_NEW:
            user_id = event.obj.message['from_id']
            text = event.obj.message.get('text', '').lower()
            
            if text in ['/start', 'старт', 'start']:
                user_data[user_id] = {
                    'blocked': False,
                    'chosen_list1': [],
                    'chosen_list2': [],
                    'current_list': 1
                }
                
                vk.messages.send(
                    user_id=user_id,
                    from_group=1,
                    message="Выбери число:",
                    keyboard=create_keyboard(user_id),
                    random_id=random.randint(1, 1000000)
                )
                print(f"✅ Кнопки отправлены пользователю {user_id}")
        
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            payload = event.obj['payload']
            user_id = event.obj['user_id']
            
            if 'num' in payload:
                selected_num = int(payload['num'])
                print(f"🔍 Получено число {selected_num}")
                
                if user_id not in user_data:
                    user_data[user_id] = {
                        'blocked': False,
                        'chosen_list1': [],
                        'chosen_list2': [],
                        'current_list': 1
                    }
                
                data = user_data[user_id]
                
                if data.get('blocked', False):
                    continue
                
                current_list = data['current_list']
                
                if current_list == 1:
                    if selected_num not in LIST_1:
                        continue
                    letter = LIST_1[selected_num]
                    data['chosen_list1'].append(selected_num)
                else:
                    if selected_num not in LIST_2:
                        continue
                    letter = LIST_2[selected_num]
                    data['chosen_list2'].append(selected_num)
                
                data['current_list'] = 2 if current_list == 1 else 1
                data['blocked'] = True
                
                vk.messages.send(
                    user_id=user_id,
                    from_group=1,
                    message=f"Выбрано число {selected_num}!\n\nВаш пункт: {letter}",
                    random_id=random.randint(1, 1000000)
                )
                print(f"✅ Отправлено")
                
                threading.Thread(target=start_timer, args=(user_id,)).start()
                
                print(f"🎲 Пользователь {user_id} выбрал {selected_num} → {letter}")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()