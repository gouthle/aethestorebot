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
# 1. CONFIGURATION
# ==========================================
API_TOKEN = os.getenv('BOT_TOKEN', '7719279464:AAHcG3fDRHAmX6jH8pTtT2_Zt6CyFhP6--8')
ADMIN_ID = int(os.getenv('ADMIN_ID', 931275762))
WEB_APP_URL = 'https://gouthle.github.io/aethestore/?v=final_stable_v20'
PORT = int(os.getenv('PORT', 8080))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ RENDER ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
    def log_message(self, format, *args): return

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', PORT), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
STRINGS = {
    'en': {
        'welcome': "Welcome to aethestore! 👋\nProfessional iPhone & Premium repair.",
        'btn_app': "🛠 Book a Repair", 'btn_about': "ℹ️ About Us", 'btn_lang': "🌐 Language",
        'about_text': "💎 <b>aethestore Service</b>\nPremium electronics repair.\n📍 Rapid on-site service in Poland.",
        'pay_msg': "Order #{} received! Please pay the deposit to confirm:",
        'pay_btn': "💳 Pay Deposit",
        'recept_msg': "💰 <b>Payment for #{}</b>\n\nSum: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nTap the button below after payment:",
        'conf_btn': "✅ I have paid",
        'thx_msg': "⏳ Request sent! The master will check and contact you soon.",
        'lang_confirm': "English language selected! 🇺🇸",
        'adm_title': "🚨 <b>NEW ORDER #{}</b>",
        'adm_device': "📱 Device: ", 'adm_phone': "📞 Phone: ", 'adm_geo': "📍 Geo: ",
        'adm_issue': "🔧 Issue: ", 'adm_user': "👤 User: ",
        'adm_confirm_btn': "✅ Confirm", 'adm_decline_btn': "❌ Decline",
        'user_confirmed': "✅ Your payment for order #{} has been CONFIRMED!",
        'user_declined': "❌ Payment for order #{} was not found.",
        'status_final': "🏁 STATUS: "
    },
    'pl': {
        'welcome': "Witaj w aethestore! 👋\nNaprawa iPhone i sprzętu premium.",
        'btn_app': "🛠 Zleć naprawę", 'btn_about': "ℹ️ O nas", 'btn_lang': "🌐 Język",
        'about_text': "💎 <b>aethestore Service</b>\nSpecjalistyczna naprawa elektroniki.\n📍 Szybki dojazd do klienta.",
        'pay_msg': "Zlecenie #{} przyjęte! Wpłać depozyt, aby potwierdzić:",
        'pay_btn': "💳 Zapłać depozyt",
        'recept_msg': "💰 <b>Płatność za #{}</b>\n\nKwota: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nKliknij po zapłaceniu:",
        'conf_btn': "✅ Zapłacone",
        'thx_msg': "⏳ Prośba wysłana! Mistrz sprawdzi wpłatę i odezwie się.",
        'lang_confirm': "Wybrano język polski! 🇵🇱",
        'adm_title': "🚨 <b>NOWE ZLECENIE #{}</b>",
        'adm_device': "📱 Urządzenie: ", 'adm_phone': "📞 Telefon: ", 'adm_geo': "📍 Lokalizacja: ",
        'adm_issue': "🔧 Problem: ", 'adm_user': "👤 Klient: ",
        'adm_confirm_btn': "✅ Potwierdź", 'adm_decline_btn': "❌ Odrzuć",
        'user_confirmed': "✅ Twoja wpłata za zlecenie #{} została POTWIERDZONA!",
        'user_declined': "❌ Płatność za zlecenie #{} nie została znaleziona.",
        'status_final': "🏁 STATUS: "
    },
    'ru': {
        'welcome': "Привет в aethestore! 👋\nРемонт iPhone и премиальной техники.",
        'btn_app': "🛠 Оформить ремонт", 'btn_about': "ℹ️ О нас", 'btn_lang': "🌐 Язык",
        'about_text': "💎 <b>aethestore Service</b>\nПрофессиональный ремонт электроники.\n📍 Быстрый выезд к клиенту.",
        'pay_msg': "Заявка #{} принята! Внесите депозит для подтверждения:",
        'pay_btn': "💳 Оплатить депозит",
        'recept_msg': "💰 <b>Оплата заказа #{}</b>\n\nСумма: <b>50 PLN</b>\n🅿️ BLIK: <code>+48 725 322 335</code>\n\nНажми после оплаты:",
        'conf_btn': "✅ Я оплатил",
        'thx_msg': "⏳ Запрос отправлен! Мастер проверит и свяжется с вами.",
        'lang_confirm': "Выбран русский язык! 🇷🇺",
        'adm_title': "🚨 <b>НОВАЯ ЗАЯВКА #{}</b>",
        'adm_device': "📱 Девайс: ", 'adm_phone': "📞 Тел: ", 'adm_geo': "📍 Гео: ",
        'adm_issue': "🔧 Проблема: ", 'adm_user': "👤 Юзер: ",
        'adm_confirm_btn': "✅ Подтвердить", 'adm_decline_btn': "❌ Отклонить",
        'user_confirmed': "✅ Ваша оплата заказа #{} ПОДТВЕРЖДЕНА!",
        'user_declined': "❌ Оплата заказа #{} не найдена.",
        'status_final': "🏁 СТАТУС: "
    }
}

user_langs = {}

def get_main_kb(uid):
    lang = user_langs.get(uid, 'en')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton(STRINGS[lang]['btn_app'], web_app=WebAppInfo(url=WEB_APP_URL)))
    markup.add(STRINGS[lang]['btn_about'], STRINGS[lang]['btn_lang'])
    return markup

def get_lang_inline(current_lang):
    kb = InlineKeyboardMarkup(row_width=1)
    for code, name in [('en', "English 🇺🇸"), ('pl', "Polski 🇵🇱"), ('ru', "Русский 🇷🇺")]:
        prefix = "✅ " if code == current_lang else ""
        kb.add(InlineKeyboardButton(f"{prefix}{name}", callback_data=f"sl_{code}"))
    return kb

@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    uid = m.from_user.id
    if uid not in user_langs: user_langs[uid] = 'en'
    await m.answer(STRINGS[user_langs[uid]]['welcome'], reply_markup=get_main_kb(uid))

@dp.message_handler(lambda m: any(m.text == STRINGS[l]['btn_lang'] for l in STRINGS))
async def show_lang_menu(m: types.Message):
    lang = user_langs.get(m.from_user.id, 'en')
    await m.answer("Choose language:", reply_markup=get_lang_inline(lang))

@dp.callback_query_handler(lambda c: c.data.startswith('sl_'))
async def callback_set_lang(c: types.CallbackQuery):
    lang = c.data.split('_')[1]
    user_langs[c.from_user.id] = lang
    await c.answer()
    await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id, reply_markup=get_lang_inline(lang))
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
        if "📍" in raw_loc:
            coords = raw_loc.replace("📍", "").strip().replace(" ", "")
            geo_link = f'<a href="https://www.google.com/maps?q={coords}">Google Maps</a>'
        else:
            geo_link = raw_loc if raw_loc else "N/A"

        report = (f"{s['adm_title'].format(oid)}\n\n{s['adm_device']}{data.get('brand')} {data.get('device')}\n"
                  f"{s['adm_phone']}<code>{data.get('phone')}</code>\n{s['adm_geo']}{geo_link}\n"
                  f"{s['adm_issue']}{data.get('problem')}\n{s['adm_user']}@{m.from_user.username}")

        adm_kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(s['adm_confirm_btn'], callback_data=f"adm_ok_{oid}_{m.from_user.id}"),
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
    await c.answer()
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton(STRINGS[lang]['conf_btn'], callback_data=f"ok_{oid}"))
    await bot.send_message(c.from_user.id, STRINGS[lang]['recept_msg'].format(oid), reply_markup=kb, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data.startswith('ok_'))
async def process_confirm(c: types.CallbackQuery):
    oid = c.data.split('_')[1]
    lang = user_langs.get(c.from_user.id, 'en')
    await c.answer()
    await bot.send_message(ADMIN_ID, f"💰 <b>BLIK CHECK!</b> Order #{oid} by @{c.from_user.username}", parse_mode="HTML")
    await bot.send_message(c.from_user.id, STRINGS[lang]['thx_msg'])

@dp.callback_query_handler(lambda c: c.data.startswith('adm_'))
async def admin_action(c: types.CallbackQuery):
    _, act, oid, cid = c.data.split('_')
    l = user_langs.get(int(cid), 'en')
    status = "✅ CONFIRMED" if act == 'ok' else "❌ DECLINED"
    await bot.send_message(int(cid), STRINGS[l]['user_confirmed' if act == 'ok' else 'user_declined'].format(oid))
    await c.answer(status)
    final_text = c.message.html_text + f"\n\n{STRINGS[l]['status_final']}<b>{status}</b>"
    await bot.edit_message_text(final_text, ADMIN_ID, c.message.message_id, parse_mode="HTML", disable_web_page_preview=True)

if __name__ == '__main__':
    print("--- aethestore Service Bot is Running ---")
    executor.start_polling(dp, skip_updates=True)