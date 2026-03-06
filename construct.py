import os
import logging
import json
import uuid
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# ==============================================================================
# 1. КОНФИГУРАЦИЯ И ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ==============================================================================

# Токен бота из BotFather
API_TOKEN = os.getenv('BOT_TOKEN', '').strip()

# Твой личный ID (узнать можно у @userinfobot)
ADMIN_ID_RAW = os.getenv('ADMIN_ID', '0').strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 0

# Ссылка на твой Mini App (GitHub Pages)
WEB_APP_URL = 'https://gouthle.github.io/aethestore/' 

# Порт для сервера (Render/Railway используют 10000 по умолчанию)
PORT = int(os.getenv('PORT', 10000))

# Глобальный статус сервиса (управляется командами /open и /close)
is_service_open = True 

# Настройка детального логирования для отладки
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Проверка наличия токена
if not API_TOKEN:
    logging.error("!!! КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN отсутствует в переменных окружения !!!")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN) if API_TOKEN else None
dp = Dispatcher(bot) if bot else None

# Временное хранилище выбранных языков пользователей
user_langs = {}

# ==============================================================================
# 2. HTTP SERVER ДЛЯ ПОДДЕРЖАНИЯ ЖИЗНИ (KEEP-ALIVE)
# ==============================================================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"AetheStore Backend is Online and Running")
    
    def log_message(self, format, *args):
        return 

def run_health_server():
    try:
        logging.info(f"Запуск Health-Check сервера на порту {PORT}...")
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        logging.error(f"Ошибка при запуске HTTP сервера: {e}")

# Запуск сервера в отдельном потоке
threading.Thread(target=run_health_server, daemon=True).start()

# ==============================================================================
# 3. ПОЛНЫЙ СЛОВАРЬ СИСТЕМНЫХ СООБЩЕНИЙ (MULTILANG)
# ==============================================================================

STRINGS = {
    'ru': {
        'welcome': "💎 <b>AetheStore Premium Service</b>\n\nПрофессиональный ремонт электроники в Кракове.\n\nНажмите кнопку ниже, чтобы заказать ремонт или узнать стоимость услуг.",
        'about_msg': "🔧 <b>AetheStore Service</b>\n\nМы — выездной сервис в Кракове. Чиним iPhone, Samsung, Xiaomi. Используем только качественные запчасти.\n\n📍 Работаем по всему городу.\n📞 Контакт: +48 725 322 335",
        'closed_msg': "\n\n🌙 <b>Сейчас мы закрыты</b>, но принимаем предзаказы! Мы свяжемся с вами в рабочее время.",
        'btn_app': "🛠 Записаться на ремонт",
        'btn_about': "ℹ️ О нас",
        'btn_lang': "🌐 Сменить язык",
        'order_ok': "✅ <b>Заявка #{} принята!</b>\n\nМастер изучит детали и свяжется с вами по номеру {} для подтверждения времени.",
        'pay_dep_btn': "💳 Внести депозит 50 PLN",
        'blik_info': "💰 <b>Оплата заказа #{}</b>\n\nСумма к оплате: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nПожалуйста, пришлите скриншот подтверждения в этот чат.",
        'adm_new': "🚨 <b>НОВЫЙ ЗАКАЗ #{}</b>",
        'adm_prio': "\n⚡ <b>ASAP PRIORITY (СРОЧНО)</b>",
        'adm_dev': "📱 Девайс: ",
        'adm_srv': "🔧 Услуга: ",
        'adm_iss': "📋 Проблема: ",
        'adm_ph': "📞 Тел: ",
        'adm_loc': "📍 Локация: ",
        'adm_prc': "💰 Цена: ",
        'adm_user': "👤 Клиент: ",
        'status': "🏁 СТАТУС: ",
        'ok': "✅ Принят",
        'no': "❌ Отказ",
        'way': "🚗 Выехал"
    },
    'en': {
        'welcome': "💎 <b>AetheStore Premium Service</b>\n\nProfessional electronics repair in Kraków.\n\nTap the button below to book a repair or check service prices.",
        'about_msg': "🔧 <b>AetheStore Service</b>\n\nOn-site repair service in Kraków. We fix iPhone, Samsung, Xiaomi.\n\n📍 We work citywide.\n📞 Contact: +48 725 322 335",
        'closed_msg': "\n\n🌙 <b>Currently closed</b>, but pre-orders are open!",
        'btn_app': "🛠 Book a Repair",
        'btn_about': "ℹ️ About Us",
        'btn_lang': "🌐 Change Language",
        'order_ok': "✅ <b>Order #{} accepted!</b>\n\nWe will call you at {} to confirm.",
        'pay_dep_btn': "💳 Pay Deposit 50 PLN",
        'blik_info': "💰 <b>Payment for #{}</b>\n\nAmount: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>",
        'adm_new': "🚨 <b>NEW ORDER #{}</b>",
        'adm_prio': "\n⚡ <b>ASAP PRIORITY</b>",
        'adm_dev': "📱 Device: ",
        'adm_srv': "🔧 Service: ",
        'adm_iss': "📋 Issue: ",
        'adm_ph': "📞 Phone: ",
        'adm_loc': "📍 Location: ",
        'adm_prc': "💰 Price: ",
        'adm_user': "👤 User: ",
        'status': "🏁 STATUS: ",
        'ok': "✅ Confirmed",
        'no': "❌ Declined",
        'way': "🚗 On way"
    },
    'pl': {
        'welcome': "💎 <b>AetheStore Premium Service</b>\n\nProfesjonalna naprawa sprzętu w Krakowie.\n\nKliknij przycisk poniżej.",
        'about_msg': "🔧 <b>AetheStore Service</b>\n\nSerwis z dojazdem w Krakowie. Naprawiamy iPhone, Samsung, Xiaomi.\n\n📍 Działamy w całym mieście.\n📞 Kontakt: +48 725 322 335",
        'closed_msg': "\n\n🌙 <b>Zamknięte</b>, ale przyjmujemy zamówienia!",
        'btn_app': "🛠 Zleć naprawę",
        'btn_about': "ℹ️ O nas",
        'btn_lang': "🌐 Zmień język",
        'order_ok': "✅ <b>Zlecenie #{} przyjęte!</b>\n\nZadzwonimy pod numer {}.",
        'dep_btn': "💳 Zapłać depozyt 50 PLN",
        'blik_info': "💰 <b>Płatność za #{}</b>\n\nKwota: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>",
        'adm_new': "🚨 <b>NOWE ZLECENIE #{}</b>",
        'adm_prio': "\n⚡ <b>ASAP PRIORITY (PILNE)</b>",
        'adm_dev': "📱 Urządzenie: ",
        'adm_srv': "🔧 Usługa: ",
        'adm_iss': "📋 Problem: ",
        'adm_ph': "📞 Telefon: ",
        'adm_loc': "📍 Lokalizacja: ",
        'adm_prc': "💰 Cena: ",
        'adm_user': "👤 Klient: ",
        'status': "🏁 STATUS: ",
        'ok': "✅ Ok",
        'no': "❌ Nie",
        'way': "🚗 Jadę"
    }
}

# ==============================================================================
# 4. ОБРАБОТЧИКИ КОМАНД И КЛАВИАТУР
# ==============================================================================

def get_main_keyboard(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton(STRINGS[lang]['btn_app'], web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.add(
        types.KeyboardButton(STRINGS[lang]['btn_about']), 
        types.KeyboardButton(STRINGS[lang]['btn_lang'])
    )
    return kb

@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    lang = m.from_user.language_code if m.from_user.language_code in STRINGS else 'ru'
    user_langs[m.from_user.id] = lang
    msg = STRINGS[lang]['welcome']
    if not is_service_open:
        msg += STRINGS[lang]['closed_msg']
    await m.answer(msg, reply_markup=get_main_keyboard(lang), parse_mode="HTML")

@dp.message_handler(lambda m: m.text in ["ℹ️ О нас", "ℹ️ About Us", "ℹ️ O nas"])
async def cmd_about(m: types.Message):
    lang = user_langs.get(m.from_user.id, 'ru')
    await m.answer(STRINGS[lang]['about_msg'], parse_mode="HTML")

@dp.message_handler(lambda m: m.text in ["🌐 Сменить язык", "🌐 Change Language", "🌐 Zmień język"])
async def cmd_lang_switch(m: types.Message):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("RU 🇷🇺", callback_data="setlang_ru"),
        InlineKeyboardButton("EN 🇺🇸", callback_data="setlang_en"),
        InlineKeyboardButton("PL 🇵🇱", callback_data="setlang_pl")
    )
    await m.answer("Выберите язык / Select language / Wybierz język:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('setlang_'))
async def process_lang_callback(c: types.CallbackQuery):
    lang = c.data.split('_')[1]
    user_langs[c.from_user.id] = lang
    await bot.send_message(c.from_user.id, "✅ Done!", reply_markup=get_main_keyboard(lang))
    await c.answer()

@dp.message_handler(commands=['open', 'close'], user_id=ADMIN_ID)
async def cmd_toggle_service(m: types.Message):
    global is_service_open
    is_service_open = (m.text == '/open')
    status_text = "ОТКРЫТО ✅" if is_service_open else "ЗАКРЫТО 🌙"
    await m.answer(f"Статус сервиса: <b>{status_text}</b>", parse_mode="HTML")

# ==============================================================================
# 5. ОБРАБОТКА ДАННЫХ ИЗ MINI APP
# ==============================================================================

@dp.message_handler(content_types='web_app_data')
async def handle_webapp_data(m: types.Message):
    try:
        data = json.loads(m.web_app_data.data)
        oid = str(uuid.uuid4())[:6].upper()
        lang = user_langs.get(m.from_user.id, 'ru')
        s = STRINGS[lang]
        
        # Расчет итоговой цены
        price = int(data.get('price', 0)) + (50 if data.get('priority') else 0)
        
        # Формирование отчета для АДМИНА
        report = (
            f"{s['adm_new'].format(oid)}\n"
            f"{s['adm_prio'] if data.get('priority') else ''}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{s['adm_dev']}<b>{data.get('brand')} {data.get('device')}</b>\n"
            f"{s['adm_srv']}<b>{data.get('service')}</b>\n"
            f"{s['adm_iss']}{data.get('problem')}\n"
            f"{s['adm_ph']}<code>{data.get('phone')}</code>\n"
            f"{s['adm_loc']}<code>{data.get('location')}</code>\n"
            f"{s['adm_prc']}<b>{price} PLN</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{s['adm_user']}@{m.from_user.username or m.from_user.id}"
        )

        adm_kb = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("✅ Ок", callback_data=f"adm_ok_{oid}_{m.from_user.id}"),
            InlineKeyboardButton("🚗 Выехал", callback_data=f"adm_way_{oid}_{m.from_user.id}"),
            InlineKeyboardButton("❌ Отказ", callback_data=f"adm_no_{oid}_{m.from_user.id}")
        )

        await bot.send_message(ADMIN_ID, report, parse_mode="HTML", reply_markup=adm_kb)
        
        pay_kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(s['dep_btn'], callback_data=f"p_{oid}")
        )
        await m.answer(s['order_ok'].format(oid, data.get('phone')), reply_markup=pay_kb, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка WebApp: {e}")
        await m.answer("⚠️ Произошла ошибка при обработке данных.")

# ==============================================================================
# 6. CALLBACK ОБРАБОТЧИКИ
# ==============================================================================

@dp.callback_query_handler(lambda c: True)
async def process_callbacks(c: types.CallbackQuery):
    lang = user_langs.get(c.from_user.id, 'ru')
    s = STRINGS[lang]

    if c.data.startswith('adm_'):
        _, act, oid, cid = c.data.split('_')
        st = s['ok'] if act == 'ok' else s['way'] if act == 'way' else s['no']
        
        await bot.send_message(int(cid), f"Заказ #{oid}: <b>{st}</b>", parse_mode="HTML")
        await c.answer(st)
        
        # Обновление сообщения админа
        new_text = c.message.html_text + f"\n\n{s['status']}<b>{st}</b>"
        await c.message.edit_text(new_text, parse_mode="HTML", reply_markup=None)

    elif c.data.startswith('p_'):
        oid = c.data.split('_')[1]
        await bot.send_message(c.from_user.id, s['blik'].format(oid), parse_mode="HTML")
        await c.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)