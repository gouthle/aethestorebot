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
# 1. CONFIGURATION & STATUS
# ==========================================
API_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID_RAW = os.getenv('ADMIN_ID', '0').strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 0

WEB_APP_URL = 'https://gouthle.github.io/aethestore/?v=final_ultra_v3'
PORT = int(os.getenv('PORT', 10000))

# Глобальный статус сервиса
is_service_open = True 

logging.basicConfig(level=logging.INFO)

if not API_TOKEN:
    logging.error("!!! КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден !!!")

bot = Bot(token=API_TOKEN) if API_TOKEN else None
dp = Dispatcher(bot) if bot else None

# --- HTTP SERVER (Keep-Alive) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"aethestore status: online")
    def log_message(self, format, *args): return

def run_server():
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        logging.error(f"Server error: {e}")

threading.Thread(target=run_server, daemon=True).start()

# --- СЛОВАРЬ ПЕРЕВОДОВ (Твой оригинал + добавки) ---
STRINGS = {
    'en': {
        'welcome': "Welcome to aethestore! 👋\nProfessional repair service.",
        'service_closed': "\n\n🌙 <b>Note: We are currently closed.</b> We will process your request tomorrow morning!",
        'btn_app': "🛠 Book a Repair", 'btn_about': "ℹ️ About Us", 'btn_lang': "🌐 Language",
        'about_text': "💎 <b>aethestore Service</b>\nPremium electronics repair.\n📍 Rapid on-site service in Poland.",
        'pay_msg': "Order #{} received! Please pay the deposit to confirm:",
        'pay_btn': "💳 Pay Deposit",
        'recept_msg': "💰 <b>Payment for #{}</b>\n\nSum: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nTap the button below after payment:",
        'conf_btn': "✅ I have paid",
        'thx_msg': "⏳ Request sent! The master will check and contact you soon.",
        'lang_confirm': "English selected! 🇺🇸",
        'adm_title': "🚨 <b>NEW ORDER #{}</b>",
        'adm_off_tag': "\n⚠️ <b>OFF-HOURS ORDER</b>",
        'adm_device': "📱 Device: ", 'adm_phone': "📞 Phone: ", 'adm_geo': "📍 Geo: ",
        'adm_issue': "🔧 Issue: ", 'adm_user': "👤 User: ",
        'adm_confirm_btn': "✅ Confirm", 'adm_decline_btn': "❌ Decline", 'adm_way_btn': "🚗 On My Way",
        'user_confirmed': "✅ Your payment for order #{} has been CONFIRMED!",
        'user_declined': "❌ Payment for order #{} was not found.",
        'user_on_way': "🚗 <b>Master is on the way!</b>\nExpect arrival in 20-40 minutes at your location.",
        'status_final': "🏁 STATUS: "
    },
    'ru': {
        'welcome': "Привет в aethestore! 👋\nРемонт iPhone и техники.",
        'service_closed': "\n\n🌙 <b>Сейчас мы закрыты.</b> Мы обработаем вашу заявку завтра утром!",
        'btn_app': "🛠 Оформить ремонт", 'btn_about': "ℹ️ О нас", 'btn_lang': "🌐 Язык",
        'about_text': "💎 <b>aethestore Service</b>\nПрофессиональный ремонт.\n📍 Выезд к клиенту по Кракову.",
        'pay_msg': "Заявка #{} принята! Внесите депозит:",
        'pay_btn': "💳 Оплатить депозит",
        'recept_msg': "💰 <b>Оплата заказа #{}</b>\n\nСумма: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nНажми после оплаты:",
        'conf_btn': "✅ Я оплатил",
        'thx_msg': "⏳ Запрос отправлен! Мастер проверит оплату.",
        'lang_confirm': "Выбран русский! 🇷🇺",
        'adm_title': "🚨 <b>НОВАЯ ЗАЯВКА #{}</b>",
        'adm_off_tag': "\n⚠️ <b>ВНЕРАБОЧЕЕ ВРЕМЯ</b>",
        'adm_device': "📱 Девайс: ", 'adm_phone': "📞 Тел: ", 'adm_geo': "📍 Гео: ",
        'adm_issue': "🔧 Проблема: ", 'adm_user': "👤 Юзер: ",
        'adm_confirm_btn': "✅ Ок", 'adm_decline_btn': "❌ Нет", 'adm_way_btn': "🚗 Выехал",
        'user_confirmed': "✅ Ваша оплата заказа #{} ПОДТВЕРЖДЕНА!",
        'user_declined': "❌ Оплата заказа #{} не найдена.",
        'user_on_way': "🚗 <b>Мастер уже выехал!</b>\nОжидайте прибытия через 20-40 минут по вашему адресу.",
        'status_final': "🏁 СТАТУС: "
    },
    'pl': {
        'welcome': "Witaj w aethestore! 👋\nNaprawa sprzętu premium.",
        'service_closed': "\n\n🌙 <b>Obecnie jesteśmy zamknięci.</b> Skontaktujemy się z Tobą jutro rano!",
        'btn_app': "🛠 Zleć naprawę", 'btn_about': "ℹ️ O nas", 'btn_lang': "🌐 Język",
        'about_text': "💎 <b>aethestore Service</b>\nSpecjalistyczna naprawa.\n📍 Szybki dojazd do klienta.",
        'pay_msg': "Zlecenie #{} przyjęte! Wpłać depozyt:",
        'pay_btn': "💳 Zapłać depozyt",
        'recept_msg': "💰 <b>Płatność za #{}</b>\n\nKwota: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nKliknij po zapłaceniu:",
        'conf_btn': "✅ Zapłacone",
        'thx_msg': "⏳ Prośba wysłana! Sprawdzamy wpłatę.",
        'lang_confirm': "Wybrano język polski! 🇵🇱",
        'adm_title': "🚨 <b>NOWE ZLECENIE #{}</b>",
        'adm_off_tag': "\n⚠️ <b>POZA GODZINAMI PRACY</b>",
        'adm_device': "📱 Urządzenie: ", 'adm_phone': "📞 Telefon: ", 'adm_geo': "📍 Lok: ",
        'adm_issue': "🔧 Problem: ", 'adm_user': "👤 Klient: ",
        'adm_confirm_btn': "✅ Ok", 'adm_decline_btn': "❌ Nie", 'adm_way_btn': "🚗 Jadę",
        'user_confirmed': "✅ Wpłata za #{} POTWIERDZONA!",
        'user_declined': "❌ Płatność za #{} nie znaleziona.",
        'user_on_way': "🚗 <b>Specjalista jest w drodze!</b>\nSpodziewaj się przyjazdu za 20-40 minut.",
        'status_final': "🏁 STATUS: "
    }
}

user_langs = {}

def get_main_kb(uid):
    lang = user_langs.get(uid, 'en')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton(STRINGS[lang]['btn_app'], web_app=WebAppInfo(url=WEB_APP_URL)))
    markup.add(STRINGS[lang]['btn_about'], STRINGS[lang]['btn_lang'])
    return markup

# --- КОМАНДЫ УПРАВЛЕНИЯ ---
@dp.message_handler(commands=['open'], user_id=ADMIN_ID)
async def cmd_open(m: types.Message):
    global is_service_open
    is_service_open = True
    await m.answer("✅ Сервис открыт!")

@dp.message_handler(commands=['close'], user_id=ADMIN_ID)
async def cmd_close(m: types.Message):
    global is_service_open
    is_service_open = False
    await m.answer("🌙 Сервис закрыт (режим отдыха).")

# --- ОСНОВНАЯ ЛОГИКА ---
@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    uid = m.from_user.id
    if uid not in user_langs: user_langs[uid] = 'en'
    text = STRINGS[user_langs[uid]]['welcome']
    if not is_service_open:
        text += STRINGS[user_langs[uid]]['service_closed']
    await m.answer(text, reply_markup=get_main_kb(uid), parse_mode="HTML")

@dp.message_handler(lambda m: any(m.text == STRINGS[l]['btn_lang'] for l in STRINGS))
async def show_lang_menu(m: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    for code, name in [('en', "🇺🇸 English"), ('pl', "🇵🇱 Polski"), ('ru', "🇷🇺 Русский")]:
        kb.add(InlineKeyboardButton(name, callback_data=f"sl_{code}"))
    await m.answer("Choose language:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('sl_'))
async def callback_set_lang(c: types.CallbackQuery):
    lang = c.data.split('_')[1]
    user_langs[c.from_user.id] = lang
    await c.answer()
    await bot.send_message(c.from_user.id, STRINGS[lang]['lang_confirm'], reply_markup=get_main_kb(c.from_user.id))

@dp.message_handler(lambda m: any(m.text == STRINGS[l]['btn_about'] for l in STRINGS))
async def cmd_about(m: types.Message):
    lang = user_langs.get(m.from_user.id, 'en')
    await m.answer(STRINGS[lang]['about_text'], parse_mode="HTML")

@dp.message_handler(content_types='web_app_data')
async def handle_webapp_data(m: types.Message):
    try:
        lang = user_langs.get(m.from_user.id, 'en')
        data = json.loads(m.web_app_data.data)
        oid = str(uuid.uuid4())[:6].upper()
        s = STRINGS[lang]
        
        raw_loc = data.get('location', '')
        geo_link = f'<a href="https://www.google.com/maps?q={raw_loc.replace("📍", "").strip()}">Google Maps 📍</a>' if "📍" in raw_loc else raw_loc
        phone = data.get('phone', '').strip()
        phone_link = f'<a href="tel:{phone}">{phone}</a>'

        report = f"{s['adm_title'].format(oid)}"
        if not is_service_open: report += s['adm_off_tag']
        
        report += (f"\n\n{s['adm_device']}<b>{data.get('brand')} {data.get('device')}</b>\n"
                  f"{s['adm_phone']}{phone_link}\n"
                  f"{s['adm_geo']}{geo_link}\n"
                  f"{s['adm_issue']}{data.get('problem')}\n"
                  f"{s['adm_user']}@{m.from_user.username or 'id'+str(m.from_user.id)}")

        adm_kb = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton(s['adm_confirm_btn'], callback_data=f"adm_ok_{oid}_{m.from_user.id}"),
            InlineKeyboardButton(s['adm_way_btn'], callback_data=f"adm_way_{oid}_{m.from_user.id}"),
            InlineKeyboardButton(s['adm_decline_btn'], callback_data=f"adm_no_{oid}_{m.from_user.id}"))

        await bot.send_message(ADMIN_ID, report, parse_mode="HTML", reply_markup=adm_kb, disable_web_page_preview=True)
        
        pay_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(s['pay_btn'], callback_data=f"p_{oid}"))
        await m.answer(s['pay_msg'].format(oid), reply_markup=pay_kb, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error WebApp Data: {e}")

@dp.callback_query_handler(lambda c: c.data.startswith('p_'))
async def process_pay(c: types.CallbackQuery):
    oid = c.data.split('_')[1]
    lang = user_langs.get(c.from_user.id, 'en')
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton(STRINGS[lang]['conf_btn'], callback_data=f"ok_{oid}"))
    await bot.send_message(c.from_user.id, STRINGS[lang]['recept_msg'].format(oid), reply_markup=kb, parse_mode="HTML")
    await c.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('ok_'))
async def process_confirm(c: types.CallbackQuery):
    oid = c.data.split('_')[1]
    lang = user_langs.get(c.from_user.id, 'en')
    await bot.send_message(ADMIN_ID, f"💰 <b>BLIK CHECK!</b> Order #{oid} by @{c.from_user.username or c.from_user.id}", parse_mode="HTML")
    await bot.send_message(c.from_user.id, STRINGS[lang]['thx_msg'])
    await c.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('adm_'))
async def admin_action(c: types.CallbackQuery):
    try:
        _, act, oid, cid = c.data.split('_')
        l = user_langs.get(int(cid), 'en')
        status = "✅ CONFIRMED" if act == 'ok' else "🚗 MASTER ON WAY" if act == 'way' else "❌ DECLINED"
        
        if act == 'ok':
            await bot.send_message(int(cid), STRINGS[l]['user_confirmed'].format(oid))
        elif act == 'way':
            await bot.send_message(int(cid), STRINGS[l]['user_on_way'], parse_mode="HTML")
        else:
            await bot.send_message(int(cid), STRINGS[l]['user_declined'].format(oid))

        await c.answer(status)
        
        # Обновляем сообщение у админа, сохраняя форматирование
        current_text = c.message.html_text.split(STRINGS[l]['status_final'])[0].strip()
        new_report = f"{current_text}\n\n{STRINGS[l]['status_final']}<b>{status}</b>"
        
        await c.message.edit_text(new_report, parse_mode="HTML", reply_markup=c.message.reply_markup, disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Admin action error: {e}")

if __name__ == '__main__':
    if dp:
        print("--- aethestore Service Bot is Running ---")
        executor.start_polling(dp, skip_updates=True)