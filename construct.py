import os
import logging
import json
import uuid
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# 1. КОНФИГУРАЦИЯ
# ==========================================
API_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
WEB_APP_URL = 'https://gouthle.github.io/aethestore/?v=final_ultra_v3'
PORT = int(os.getenv('PORT', 10000))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN) if API_TOKEN else None
dp = Dispatcher(bot) if bot else None

# --- Хранилище (в памяти) ---
user_data = {} # {user_id: {'lang': 'en', 'orders': []}}

# --- HTTP SERVER (Keep-Alive) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"aethestore status: online")
    def log_message(self, format, *args): return

def run_server():
    HTTPServer(('0.0.0.0', PORT), HealthCheckHandler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- СЛОВАРЬ ПЕРЕВОДОВ (Добавлен польский и улучшен русский) ---
STRINGS = {
    'en': {
        'welcome': "Welcome to aethestore! 👋\nHow can we help you today?",
        'btn_app': "🛠 Book a Repair", 'btn_about': "ℹ️ About Us", 'btn_lang': "🌐 Language",
        'about_text': "💎 <b>aethestore Service</b>\nPremium electronics repair in Kraków.\n📍 We come to you!",
        'pay_msg': "Order #<b>{}</b> received! Please pay the deposit to confirm:",
        'pay_btn': "💳 Pay Deposit 50 PLN",
        'recept_msg': "💰 <b>Payment #{}</b>\n\nBLIK: <code>+48 725 322 335</code>\n\nTap the button after payment:",
        'conf_btn': "✅ I have paid",
        'thx_msg': "⏳ Processing! Master will contact you shortly.",
        'lang_confirm': "English selected! 🇺🇸",
        'status_final': "🏁 STATUS: "
    },
    'ru': {
        'welcome': "Добро пожаловать в aethestore! 👋\nЧем можем помочь?",
        'btn_app': "🛠 Оформить ремонт", 'btn_about': "ℹ️ О нас", 'btn_lang': "🌐 Язык",
        'about_text': "💎 <b>aethestore Service</b>\nПрофессиональный ремонт в Кракове.\n📍 Мастер выезжает к вам!",
        'pay_msg': "Заявка #<b>{}</b> принята! Внесите депозит для подтверждения:",
        'pay_btn': "💳 Оплатить 50 PLN",
        'recept_msg': "💰 <b>Оплата заказа #{}</b>\n\nBLIK: <code>+48 725 322 335</code>\n\nНажмите после оплаты:",
        'conf_btn': "✅ Я оплатил",
        'thx_msg': "⏳ Обработка! Мастер проверит оплату и свяжется с вами.",
        'lang_confirm': "Выбран русский язык! 🇷🇺",
        'status_final': "🏁 СТАТУС: "
    },
    'pl': {
        'welcome': "Witaj w aethestore! 👋\nW czym możemy pomóc?",
        'btn_app': "🛠 Zleć naprawę", 'btn_about': "ℹ️ O nas", 'btn_lang': "🌐 Język",
        'about_text': "💎 <b>aethestore Service</b>\nProfesjonalna naprawa w Krakowie.\n📍 Dojazd do klienta!",
        'pay_msg': "Zlecenie #<b>{}</b> przyjęte! Wpłać depozyt, aby potwierdzić:",
        'pay_btn': "💳 Zapłać 50 PLN",
        'recept_msg': "💰 <b>Płatność za #{}</b>\n\nBLIK: <code>+48 725 322 335</code>\n\nKliknij po zapłaceniu:",
        'conf_btn': "✅ Zapłacone",
        'thx_msg': "⏳ Przetwarzanie! Specjalista odezwie się wkrótce.",
        'lang_confirm': "Wybrano język polski! 🇵🇱",
        'status_final': "🏁 STATUS: "
    }
}

# --- ЛОГИКА БОТА ---

def get_lang(uid):
    return user_data.get(uid, {}).get('lang', 'en')

def get_main_kb(uid):
    lang = get_lang(uid)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton(STRINGS[lang]['btn_app'], web_app=WebAppInfo(url=WEB_APP_URL)))
    markup.add(STRINGS[lang]['btn_about'], STRINGS[lang]['btn_lang'])
    return markup

@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    uid = m.from_user.id
    if uid not in user_data:
        user_data[uid] = {'lang': 'en'}
    await m.answer(STRINGS[get_lang(uid)]['welcome'], reply_markup=get_main_kb(uid))

@dp.message_handler(lambda m: any(m.text == STRINGS[l]['btn_lang'] for l in STRINGS))
async def show_lang_menu(m: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🇺🇸 English", callback_data="sl_en"))
    kb.add(InlineKeyboardButton("🇵🇱 Polski", callback_data="sl_pl"))
    kb.add(InlineKeyboardButton("🇷🇺 Русский", callback_data="sl_ru"))
    await m.answer("Select your language / Wybierz język / Выберите язык:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('sl_'))
async def set_lang(c: types.CallbackQuery):
    lang = c.data.split('_')[1]
    user_data[c.from_user.id] = {'lang': lang}
    await c.answer()
    await bot.send_message(c.from_user.id, STRINGS[lang]['lang_confirm'], reply_markup=get_main_kb(c.from_user.id))

@dp.message_handler(content_types='web_app_data')
async def handle_data(m: types.Message):
    try:
        lang = get_lang(m.from_user.id)
        data = json.loads(m.web_app_data.data)
        oid = str(uuid.uuid4())[:6].upper()
        
        # Формируем красивую ссылку на карты, если есть координаты
        loc = data.get('location', '—')
        if '📍' in loc:
            clean_loc = loc.replace('📍', '').strip()
            loc_link = f'<a href="https://www.google.com/maps?q={clean_loc}">Google Maps 📍</a>'
        else:
            loc_link = loc

        report = (f"🚨 <b>NEW ORDER #{oid}</b>\n\n"
                  f"📱 Device: <b>{data.get('brand')} {data.get('device')}</b>\n"
                  f"📞 Phone: <code>{data.get('phone')}</code>\n"
                  f"📍 Location: {loc_link}\n"
                  f"🔧 Issue: {data.get('problem')}\n"
                  f"👤 User: @{m.from_user.username or 'no_name'}")

        kb = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("✅ OK", callback_data=f"adm_ok_{oid}_{m.from_user.id}"),
            InlineKeyboardButton("🚗 WAY", callback_data=f"adm_way_{oid}_{m.from_user.id}"),
            InlineKeyboardButton("❌ NO", callback_data=f"adm_no_{oid}_{m.from_user.id}"))

        await bot.send_message(ADMIN_ID, report, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
        
        pay_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(STRINGS[lang]['pay_btn'], callback_data=f"pay_{oid}"))
        await m.answer(STRINGS[lang]['pay_msg'].format(oid), reply_markup=pay_kb, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error: {e}")

@dp.callback_query_handler(lambda c: c.data.startswith('adm_'))
async def admin_control(c: types.CallbackQuery):
    _, act, oid, cid = c.data.split('_')
    l = get_lang(int(cid))
    
    # Тексты статусов для админа
    status_text = "✅ CONFIRMED" if act == 'ok' else "🚗 MASTER ON WAY" if act == 'way' else "❌ DECLINED"
    
    # Уведомление пользователя
    if act == 'ok':
        await bot.send_message(cid, f"✅ Order #{oid}: Payment Confirmed!")
    elif act == 'way':
        await bot.send_message(cid, "🚗 Master is on the way! Arrival in 20-40 min.")
    
    await c.answer(status_text)
    
    # Обновляем сообщение у админа (красивая пересборка)
    new_text = c.message.html_text.split("🏁")[0].strip() # Убираем старый статус, если он был
    new_text += f"\n\n🏁 <b>STATUS: {status_text}</b>"
    
    await c.message.edit_text(new_text, parse_mode="HTML", reply_markup=c.message.reply_markup, disable_web_page_preview=True)

if __name__ == '__main__':
    if dp:
        executor.start_polling(dp, skip_updates=True)