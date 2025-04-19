from keep_alive import keep_alive
keep_alive()
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
from googletrans import Translator
from bs4 import BeautifulSoup
import threading
import time
# القطاعات المحددة لمراقبة السيولة
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
‎# دالة جلب بيانات Binance
def fetch_binance_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("فشل في جلب البيانات من Binance")
            return []
    except Exception as e:
        print("خطأ أثناء الاتصال بـ Binance:", e)
        return []
def analyze_sectors_volume(data):
    sector_volumes = {sector: 0 for sector in WATCHED_SECTORS}

    for item in data:
        symbol = item.get("symbol", "")
        volume = float(item.get("quoteVolume", 0))

        for sector in WATCHED_SECTORS:
            if sector.lower().replace(" ", "") in symbol.lower():
                sector_volumes[sector] += volume

‎    # ترتيب أعلى القطاعات ضخًا
    sorted_sectors = sorted(sector_volumes.items(), key=lambda x: x[1], reverse=True)

    return sorted_sectors
‎# دالة إرسال تنبيه عند تغيّر السيولة في القطاعات
def send_sector_alerts(context: CallbackContext):
    data = fetch_binance_data()
    if not data:
        return

    sorted_sectors = analyze_sectors_volume(data)

    message = "تنبيه: تحرك السيولة في القطاعات التالية:\n"
    for sector, volume in sorted_sectors[:5]:
        if volume > 0:
            message += f"• {sector}: {volume:,.0f} USDT\n"

    if "السيولة" not in context.chat_data.get("last_alert", ""):
        context.bot.send_message(chat_id=context.job.context, text=message)
        context.chat_data["last_alert"] = "السيولة"
‎‎# دالة مقارنة التغيرات وإرسال تنبيهات متعددة
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
‎# تشغيل التنبيهات التلقائية للسيولة كل 60 ثانية
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
            time.sleep(60)
    threading.Thread(target=monitor).start()
# توكن البوت
TELEGRAM_BOT_TOKEN = '7651191638:AAHYogMKCm4mkOJKPe1U7-sVlcL70Rin0LA'

# مفتاح NewsAPI
NEWS_API_KEY = '71dee0f842b54a0e89f4d738852bdcab'

# الكلمات المفتاحية
KEYWORDS = ['Trump', 'ترامب', 'China', 'الصين', 'crypto', 'cryptocurrency', 'bitcoin',     'BTC','USD', 'الدولار', 'الين الياباني', 'الين', 'الأسهم', 'stock', 'forex', 'إيلون ماسك', 'Elon Musk']

translator = Translator()

def fetch_news():
    query = ' OR '.join(KEYWORDS)
    url = (
        f"https://newsapi.org/v2/everything?q={query}"
        f"&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    )
    try:
        response = requests.get(url)
        articles = response.json().get('articles', [])[:8]
        news_list = []

        for article in articles:
            title = article.get('title', '')
            url = article.get('url', '')
            content = f"{title}\n{url}"
            translated = translator.translate(content, dest='ar').text
            news_list.append(translated)

        return news_list if news_list else ["لم يتم العثور على أخبار حالياً."]
    except Exception as e:
        return [f"فشل في جلب الأخبار: {e}"]

def check_binance_new_listings():
        url = "https://www.binance.com/en/support/announcement/c-48?navId=48"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('a')
                listings = []
                for article in articles:
                        title = article.get_text()
                        href = article.get('href')
                        if "Will List" in title or "Binance Launchpool" in title:
                                listings.append(f"{title}\nhttps://www.binance.com{href}")
                return listings[:5] if listings else ["لا توجد عملات جديدة حالياً."]
        except Exception as e:
                return [f"فشل في جلب إدراجات Binance: {e}"]

def check_cmc_listings():
    try:
        url = "https://coinmarketcap.com/new/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('table tbody tr')[:5]
        listings = []
        for row in rows:
             name = row.select_one('a.cmc-link').text.strip()
             link = "https://coinmarketcap.com" + row.select_one('a.cmc-link')['href']
             listings.append(f"عملة جديدة على CoinMarketCap: {name}\n{link}")
        return listings if listings else ["لا توجد إدراجات جديدة حالياً على CoinMarketCap."]
    except Exception as e:
        return [f"فشل في جلب إدراجات CoinMarketCap: {e}"]

def check_coingecko_listings():
     try:
         url = "https://www.coingecko.com/en/coins/recently_added"
         headers = {'User-Agent': 'Mozilla/5.0'}
         response = requests.get(url, headers=headers)
         soup = BeautifulSoup(response.text, 'html.parser')
         rows = soup.select('table tbody tr')[:5]
         listings = []
         for row in rows:
             name = row.select_one('a.tw-hidden').text.strip()
             link = "https://www.coingecko.com" + row.select_one('a.tw-hidden')['href']
             listings.append(f"عملة جديدة على CoinGecko: {name}\n{link}")
         return listings if listings else ["لا توجد إدراجات جديدة حالياً على CoinGecko."]
     except Exception as e:
         return [f"فشل في جلب إدراجات CoinGecko: {e}"]

def start(update, context):
      update.message.reply_text("أهلاً بك! هذا البوت يجلب لك آخر أخبار السوق والإدراجات الجديدة تلقائياً.")

def news(update, context):
      for item in fetch_news():
          update.message.reply_text(item)
  
def listings(update, context):
    for item in check_binance_new_listings():
         update.message.reply_text(item)
    for item in check_cmc_listings():
         update.message.reply_text(item)
    for item in check_coingecko_listings():
         update.message.reply_text(item)

def start_auto_tasks(update, context):
    update.message.reply_text("تم تفعيل التنبيهات التلقائية.")
    threading.Thread(target=run_tasks, args=(update, context)).start()

def run_tasks(update, context):
    while True:
        try:
            for item in fetch_news():
                context.bot.send_message(chat_id=update.effective_chat.id, text=item)
            for item in check_binance_new_listings():
                context.bot.send_message(chat_id=update.effective_chat.id, text=item)
            for item in check_cmc_listings():
                context.bot.send_message(chat_id=update.effective_chat.id, text=item)
            for item in check_coingecko_listings():
                context.bot.send_message(chat_id=update.effective_chat.id, text=item)
            time.sleep(60)
        except Exception as e:
                context.bot.send_message(chat_id=update.effective_chat.id, text="حدث خطأ:\n" + str(e))
        break

# إعداد البوت
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# أوامر البوت
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", news))
dispatcher.add_handler(CommandHandler("listings", listings))
dispatcher.add_handler(CommandHandler("auto", auto))
def auto(update: Update, context: CallbackContext):
    update.message.reply_text("تم تفعيل المراقبة التلقائية للسيولة.")
    chat_id = update.effective_chat.id
    start_auto_sector_monitoring(context.bot, chat_id)
# تشغيل البوت
updater.start_polling()
updater.idle()
