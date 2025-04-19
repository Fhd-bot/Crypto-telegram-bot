from keep_alive import keep_alive
keep_alive()

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import threading
import time

# القطاعات لمراقبة السيولة
WATCHED_SECTORS = {
    "AI": [],
    "DeFi": [],
    "BNB Chain": [],
    "Gaming": [],
    "Solana": [],
    "Meme": [],
    "Megadrop": [],
    "RWA": [],
    "البنية التحتية": [],
    "الطبقة 1 / الطبقة 2": [],
    "مجمع الإطلاق": []
}

# CoinGlass mock-up (سيتم تطويره لاحقاً)
def check_coinglass_alerts():
    try:
        return "تنبيه CoinGlass: تصفيات مرتفعة في السوق! راقب التحركات."
    except:
        return None

# بيانات Binance
def fetch_binance_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def analyze_sectors_volume(data):
    sector_volumes = {sector: 0 for sector in WATCHED_SECTORS}
    for item in data:
        symbol = item.get("symbol", "")
        volume = float(item.get("quoteVolume", 0))
        for sector in WATCHED_SECTORS:
            if sector.lower().replace(" ", "") in symbol.lower():
                sector_volumes[sector] += volume
    return sector_volumes

def check_sector_volume_change(bot, chat_id, previous_volumes, current_volumes, threshold=15):
    alerts = []
    for sector, current_volume in current_volumes.items():
        previous_volume = previous_volumes.get(sector, 0)
        if previous_volume == 0:
            continue
        change_percent = ((current_volume - previous_volume) / previous_volume) * 100
        if change_percent >= threshold:
            alerts.append(f"نمو سيولة كبير في قطاع: {sector} بنسبة {change_percent:.2f}%")
    if alerts:
        message = "\n".join(alerts)
        bot.send_message(chat_id=chat_id, text=message)

def start_auto_sector_monitoring(bot, chat_id):
    def monitor():
        previous_volumes = {}
        while True:
            data = fetch_binance_data()
            if not data:
                time.sleep(60)
                continue
            current_volumes = analyze_sectors_volume(data)
            check_sector_volume_change(bot, chat_id, previous_volumes, current_volumes)
            previous_volumes = current_volumes
            time.sleep(120)
    threading.Thread(target=monitor).start()

# CoinGecko Top 20
def fetch_top_20_binance():
    url = "https://api.coingecko.com/api/v3/exchanges/binance/tickers"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            tickers = response.json().get("tickers", [])
            sorted_tickers = sorted(tickers, key=lambda x: x.get("converted_volume", {}).get("usd", 0), reverse=True)
            return [t["base"] for t in sorted_tickers[:20]]
    except:
        pass
    return []

previous_top_20 = []

def monitor_top_20(bot, chat_id):
    global previous_top_20
    while True:
        current_top_20 = fetch_top_20_binance()
        new_entries = [coin for coin in current_top_20 if coin not in previous_top_20]
        if new_entries:
            message = "🚀 عملات دخلت توب 20 في Binance:\n" + "\n".join(new_entries)
            bot.send_message(chat_id=chat_id, text=message)
        previous_top_20 = current_top_20
        time.sleep(180)

# تفعيل البوت
TELEGRAM_BOT_TOKEN = "7744121184:AAG_B_DXMV56dqeMPjWt163hbPsgH_y2B0k"

def start(update, context):
    update.message.reply_text("أهلاً بك! البوت يراقب السيولة، CoinGecko، و CoinGlass.")

def auto(update, context):
    chat_id = update.effective_chat.id
    update.message.reply_text("تم تفعيل المراقبة التلقائية لكل المؤشرات.")
    threading.Thread(target=start_auto_sector_monitoring, args=(context.bot, chat_id)).start()
    threading.Thread(target=monitor_top_20, args=(context.bot, chat_id)).start()
def coin_glass():
        while True:
            alert = check_coinglass_alerts()
            if alert:
                context.bot.send_message(chat_id=chat_id, text=alert)
            time.sleep(300)
            threading.Thread(target=coin_glass).start()

updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("auto", auto))
updater.start_polling()
updater.idle()
