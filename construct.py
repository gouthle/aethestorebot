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

API_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID_RAW = os.getenv('ADMIN_ID', '0').strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 0

WEB_APP_URL = 'https://gouthle.github.io/aethestore/' 
PORT = int(os.getenv('PORT', 10000))

is_service_open = True 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if not API_TOKEN:
    logging.error("!!! КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN отсутствует в переменных окружения !!!")

bot = Bot(token=API_TOKEN) if API_TOKEN else None
dp = Dispatcher(bot) if bot else None

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

threading.Thread(target=run_health_server, daemon=True).start()

# ==============================================================================
# 3. ПОЛНЫЙ СЛОВАРЬ СИСТЕМНЫХ СООБЩЕНИЙ (MULTILANG)
# ==============================================================================

STRINGS = {
    'ru': {
        'welcome': "💎 <b>AetheStore Premium Service</b>\n\nПрофессиональный ремонт электроники в Кракове.\n\nНажмите кнопку ниже, чтобы заказать ремонт или узнать стоимость услуг.",
        'closed_msg': "\n\n🌙 <b>Сейчас мы закрыты</b>, но принимаем предзаказы! Мы свяжемся с вами в рабочее время.",
        'btn_app': "🛠 Оформить ремонт",
        'order_ok': "✅ <b>Заявка #{} принята!</b>\n\nМастер изучит детали и свяжется с вами по номеру {} для подтверждения времени.",
        'dep_btn': "💳 Внести депозит 50 PLN",
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
        'closed_msg': "\n\n🌙 <b>We are currently closed</b>, but we accept pre-orders! We will contact you during business hours.",
        'btn_app': "🛠 Book a Repair",
        'order_ok': "✅ <b>Order #{} accepted!</b>\n\nThe technician will call you at {} to confirm the appointment time.",
        'dep_btn': "💳 Pay Deposit 50 PLN",
        'blik_info': "💰 <b>Payment for #{}</b>\n\nAmount: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nPlease send a screenshot of the payment here.",
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
        'way': "🚗 On my way"
    },
    'pl': {
        'welcome': "💎 <b>AetheStore Premium Service</b>\n\nProfesjonalna naprawa sprzętu w Krakowie.\n\nKliknij przycisk poniżej, aby zamówić naprawę lub sprawdzić cennik.",
        'closed_msg': "\n\n🌙 <b>Obecnie jesteśmy zamknięci</b>, ale przyjmujemy zamówienia! Skontaktujemy się z Tobą rano.",
        'btn_app': "🛠 Zleć naprawę",
        'order_ok': "✅ <b>Zlecenie #{} przyjęte!</b>\n\nZadzwonimy pod numer {} w celu ustalenia godziny wizyty.",
        'dep_btn': "💳 Zapłać depozyt 50 PLN",
        'blik_info': "💰 <b>Płatność za #{}</b>\n\nKwota: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nProsimy o przesłanie potwierdzenia płatności w tej wiadomości.",
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
        'ok': "✅ Przyjęte",
        'no': "❌ Odrzucone",
        'way': "🚗 Specjalista jedzie"
    }
}

# ==============================================================================
# 4. ОБРАБОТЧИКИ БАЗОВЫХ КОМАНД
# ==============================================================================

@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    uid = m.from_user.id
    lang = m.from_user.language_code if m.from_user.language_code in STRINGS else 'ru'
    user_langs[uid] = lang
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(STRINGS[lang]['btn_app'], web_app=WebAppInfo(url=WEB_APP_URL)))
    
    msg = STRINGS[lang]['welcome']
    if not is_service_open:
        msg += STRINGS[lang]['closed_msg']
        
    await m.answer(msg, reply_markup=kb, parse_mode="HTML")

@dp.message_handler(commands=['open', 'close'], user_id=ADMIN_ID)
async def cmd_toggle_service(m: types.Message):
    global is_service_open
    is_service_open = (m.text == '/open')
    status_text = "ОТКРЫТО ✅" if is_service_open else "ЗАКРЫТО 🌙"
    await m.answer(f"Статус сервиса успешно обновлен: <b>{status_text}</b>", parse_mode="HTML")

# ==============================================================================
# 5. ОБРАБОТКА ДАННЫХ ИЗ MINI APP (WEB APP DATA)
# ==============================================================================

@dp.message_handler(content_types='web_app_data')
async def handle_webapp_data(m: types.Message):
    try:
        lang = user_langs.get(m.from_user.id, 'ru')
        s = STRINGS[lang]
        
        data = json.loads(m.web_app_data.data)
        oid = str(uuid.uuid4())[:6].upper()
        
        # Подсчет итоговой цены
        base_price = int(data.get('price', 0))
        priority_fee = 50 if data.get('priority') else 0
        total_price = base_price + priority_fee
        
        # Получаем выбранную услугу (карточку)
        chosen_service = data.get('service', 'General Service')

        # Формируем детальный отчет для Админа
        # ДОБАВЛЕНО: Вывод услуги жирным шрифтом
        report = (
            f"{s['adm_new'].format(oid)}"
            f"{s['adm_prio'] if data.get('priority') else ''}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{s['adm_dev']}<b>{data.get('brand')} {data.get('device')}</b>\n"
            f"{s['adm_srv']}<b>{chosen_service}</b>\n"
            f"{s['adm_iss']}{data.get('problem')}\n"
            f"{s['adm_ph']}<code>{data.get('phone')}</code>\n"
            f"{s['adm_loc']}<code>{data.get('location')}</code>\n"
            f"{s['adm_prc']}<b>{total_price} PLN</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{s['adm_user']}@{m.from_user.username or m.from_user.id}"
        )

        adm_kb = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("✅ Ок", callback_data=f"adm_ok_{oid}_{m.from_user.id}"),
            InlineKeyboardButton("🚗 Выехал", callback_data=f"adm_way_{oid}_{m.from_user.id}"),
            InlineKeyboardButton("❌ Отказ", callback_data=f"adm_no_{oid}_{m.from_user.id}")
        )

        await bot.send_message(ADMIN_ID, report, parse_mode="HTML", reply_markup=adm_kb)

        client_kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(s['pay_dep_btn'], callback_data=f"user_pay_{oid}")
        )
        await m.answer(s['order_ok'].format(oid, data.get('phone')), reply_markup=client_kb, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка при обработке WebApp данных: {e}")
        await m.answer("⚠️ Произошла техническая ошибка. Пожалуйста, попробуйте еще раз.")

# ==============================================================================
# 6. ОБРАБОТКА CALLBACK КНОПОК (КНОПКИ В ЧАТЕ)
# ==============================================================================

@dp.callback_query_handler(lambda c: True)
async def process_all_callbacks(c: types.CallbackQuery):
    lang = user_langs.get(c.from_user.id, 'ru')
    s = STRINGS[lang]

    if c.data.startswith('adm_'):
        _, act, oid, cid = c.data.split('_')
        status_label = s['ok'] if act == 'ok' else s['way'] if act == 'way' else s['no']
        
        client_notification = f"Заказ #{oid}: <b>{status_label}</b>"
        if act == 'way':
            client_notification += f"\n{s['way']}. Ожидайте мастера в течение часа."
            
        await bot.send_message(int(cid), client_notification, parse_mode="HTML")
        await c.answer(status_label)
        
        new_admin_text = c.message.html_text + f"\n\n{s['status']}<b>{status_label}</b>"
        await c.message.edit_text(new_admin_text, parse_mode="HTML", reply_markup=None)

    elif c.data.startswith('user_pay_'):
        oid = c.data.split('_')[2]
        await bot.send_message(c.from_user.id, s['blik_info'].format(oid), parse_mode="HTML")
        await c.answer()

# ==============================================================================
# 7. ЗАПУСК БОТА
# ==============================================================================

if __name__ == '__main__':
    if dp:
        logging.info("--- AetheStore Premium Bot Started Successfully ---")
        executor.start_polling(dp, skip_updates=True)