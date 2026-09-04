import os
import requests
import pandas as pd
import sqlite3
import pandas_ta as ta

RTL_MARK = "\u200f"
SUPPORTED_COINS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "doge": "dogecoin",
}
AI_MODELS_FALLBACK = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "openrouter/free",
]
from database import init_db, add_user_if_not_exists, get_favorite_coins, set_favorite_coins
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user_if_not_exists(chat_id)

    keyboard = [
        [
            InlineKeyboardButton("📊 تحلیل BTC", callback_data="analysis_btc"),
            InlineKeyboardButton("📊 تحلیل ETH", callback_data="analysis_eth"),
        ],
        [
            InlineKeyboardButton("📊 تحلیل SOL", callback_data="analysis_sol"),
            InlineKeyboardButton("💰 قیمت BTC", callback_data="price_btc"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "سلام! من بات تحلیل کریپتو هستم. 🤖\nیکی از گزینه‌ها رو انتخاب کن، یا هر سوالی داری بپرس:",
        reply_markup=reply_markup,
    )



def get_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        btc_price = data["bitcoin"]["usd"]
        return btc_price
    except:
        return None

def get_coin_history(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": "30", "interval": "daily"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        prices = data["prices"]
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        return df
    except:
        return None

def get_coin_analysis(coin_id):
    df = get_coin_history(coin_id)
    if df is None:
        return None

    df["rsi"] = ta.rsi(df["price"], length=14)
    df["sma_7"] = ta.sma(df["price"], length=7)
    df["sma_25"] = ta.sma(df["price"], length=25)

    latest = df.iloc[-1]

    return {
        "price": latest["price"],
        "rsi": latest["rsi"],
        "sma_7": latest["sma_7"],
        "sma_25": latest["sma_25"],
    }
    
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btc_price = get_btc_price()
    if btc_price is None:
        await update.message.reply_text("متأسفم، الان نتونستم قیمت رو بگیرم. لطفاً چند لحظه دیگه دوباره امتحان کن.")
    else:
        await update.message.reply_text(f"قیمت لحظه‌ای بیت‌کوین: ${btc_price:,}")



async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "تو یک دستیار تحلیل بازار کریپتو هستی. همیشه به فارسی جواب بده. "
                            "تحلیل‌هات رو بر اساس اطلاعات آماری ارائه بده، نه پیش‌بینی قطعی. "
                            "همیشه یادآوری کن که این توصیه‌ی مالی نیست."
                        ),
                    },
                    {"role": "user", "content": user_message},
                ],
            },
            timeout=30,
        )
        data = response.json()
        ai_reply = data["choices"][0]["message"]["content"]
        await update.message.reply_text(ai_reply)
    except Exception as e:
        print(f"AI error: {e}")
        await update.message.reply_text("متأسفم، الان نتونستم جواب بدم. دوباره امتحان کن.")

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # گرفتن ورودی کاربر، مثلاً از "/analysis eth" کلمه‌ی "eth" رو می‌گیریم
    if context.args:
        symbol = context.args[0].lower()
    else:
        symbol = "btc"  # اگه کاربر چیزی ننویسه، پیش‌فرض بیت‌کوین باشه

    if symbol not in SUPPORTED_COINS:
        supported_list = ", ".join(SUPPORTED_COINS.keys())
        await update.message.reply_text(
            f"این ارز رو نمی‌شناسم. ارزهای پشتیبانی‌شده: {supported_list}"
        )
        return

    coin_id = SUPPORTED_COINS[symbol]
    data = get_coin_analysis(coin_id)

    if data is None:
        await update.message.reply_text("متأسفم، الان نتونستم داده‌ها رو بگیرم. لطفاً چند لحظه دیگه دوباره امتحان کن.")
        return

    price = data["price"]
    rsi = data["rsi"]
    sma_7 = data["sma_7"]
    sma_25 = data["sma_25"]

    if rsi > 70:
        rsi_note = "نسبتاً بالا (احتمال اشباع خرید)"
    elif rsi < 30:
        rsi_note = "نسبتاً پایین (احتمال اشباع فروش)"
    else:
        rsi_note = "در محدوده‌ی عادی"

    if sma_7 > sma_25:
        trend_note = "روند کوتاه‌مدت صعودی به نظر می‌رسه"
    else:
        trend_note = "روند کوتاه‌مدت نزولی به نظر می‌رسه"

    message = (
        f"📊 تحلیل {symbol.upper()}\n\n"
        f"قیمت فعلی: ${price:,.2f}\n"
        f"RSI (۱۴ روزه): {rsi:.1f} — {rsi_note}\n"
        f"میانگین ۷ روزه: ${sma_7:,.2f}\n"
        f"میانگین ۲۵ روزه: ${sma_25:,.2f}\n"
        f"→ {trend_note}\n\n"
        f"⚠️ این تحلیل صرفاً بر اساس داده‌های آماری گذشته‌ست و توصیه‌ی مالی محسوب نمی‌شه. "
        f"تصمیم‌گیری نهایی و مسئولیت آن با خودتونه."
    )

    await update.message.reply_text(message)

async def my_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    coins = get_favorite_coins(chat_id)
    await update.message.reply_text(f"کوین‌های موردعلاقه‌ی فعلی تو: {', '.join(coins)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, symbol = query.data.split("_")

    if action == "price" and symbol == "btc":
        btc_price = get_btc_price()
        if btc_price:
            await query.message.reply_text(f"قیمت لحظه‌ای بیت‌کوین: ${btc_price:,}")
        else:
            await query.message.reply_text("متأسفم، الان نتونستم قیمت رو بگیرم.")
        return

    if action == "analysis":
        if symbol not in SUPPORTED_COINS:
            await query.message.reply_text("این ارز پشتیبانی نمی‌شه.")
            return

        coin_id = SUPPORTED_COINS[symbol]
        data = get_coin_analysis(coin_id)

        if data is None:
            await query.message.reply_text("متأسفم، الان نتونستم داده‌ها رو بگیرم.")
            return

        price = data["price"]
        rsi = data["rsi"]
        sma_7 = data["sma_7"]
        sma_25 = data["sma_25"]

        if rsi > 70:
            rsi_note = "نسبتاً بالا (احتمال اشباع خرید)"
        elif rsi < 30:
            rsi_note = "نسبتاً پایین (احتمال اشباع فروش)"
        else:
            rsi_note = "در محدوده‌ی عادی"

        trend_note = "روند کوتاه‌مدت صعودی به نظر می‌رسه" if sma_7 > sma_25 else "روند کوتاه‌مدت نزولی به نظر می‌رسه"

        message = (
            f"📊 تحلیل {symbol.upper()}\n\n"
            f"قیمت فعلی: ${price:,.2f}\n"
            f"RSI (۱۴ روزه): {rsi:.1f} — {rsi_note}\n"
            f"میانگین ۷ روزه: ${sma_7:,.2f}\n"
            f"میانگین ۲۵ روزه: ${sma_25:,.2f}\n"
            f"→ {trend_note}\n\n"
            f"⚠️ این تحلیل صرفاً بر اساس داده‌های آماری گذشته‌ست و توصیه‌ی مالی محسوب نمی‌شه."
        )

        await query.message.reply_text(message)

async def send_daily_report(app):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, favorite_coins FROM users")
    all_users = cursor.fetchall()
    conn.close()

    for chat_id, favorite_coins_str in all_users:
        coins = favorite_coins_str.split(",")
        report_lines = ["📅 گزارش روزانه‌ی بازار\n"]

        for symbol in coins:
            if symbol not in SUPPORTED_COINS:
                continue
            coin_id = SUPPORTED_COINS[symbol]
            data = get_coin_analysis(coin_id)
            if data is None:
                continue

            rsi_note = "اشباع خرید" if data["rsi"] > 70 else "اشباع فروش" if data["rsi"] < 30 else "عادی"
            report_lines.append(
                f"{symbol.upper()}: ${data['price']:,.2f} | RSI: {data['rsi']:.1f} ({rsi_note})"
            )

        report_lines.append("\n⚠️ این گزارش توصیه‌ی مالی نیست.")
        report_text = "\n".join(report_lines)

        try:
            await app.bot.send_message(chat_id=chat_id, text=report_text)
        except Exception as e:
            print(f"Failed to send report to {chat_id}: {e}")

async def set_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text(
            "لطفاً کوین‌های موردعلاقه‌تو با فاصله بنویس، مثلاً:\n/setcoins btc eth sol"
        )
        return

    requested_coins = [c.lower() for c in context.args]
    invalid_coins = [c for c in requested_coins if c not in SUPPORTED_COINS]

    if invalid_coins:
        await update.message.reply_text(
            f"این ارزها رو نمی‌شناسم: {', '.join(invalid_coins)}\n"
            f"ارزهای پشتیبانی‌شده: {', '.join(SUPPORTED_COINS.keys())}"
        )
        return

    set_favorite_coins(chat_id, requested_coins)
    await update.message.reply_text(
        f"✅ کوین‌های موردعلاقه‌ت ذخیره شد: {', '.join(requested_coins)}"
    )
def call_ai_model(full_prompt):
    system_prompt = (
        "تو یک دستیار تحلیل بازار کریپتو هستی که در تلگرام چت می‌کنه. "
        "همیشه به زبان فارسی روان و طبیعی پاسخ بده. "
        "پاسخت رو کوتاه و خودمونی نگه دار، در حد یک یا دو پاراگراف کوتاه، بدون تیتر یا شماره‌گذاری زیاد. "
        "وقتی داده‌های آماری واقعی (قیمت، RSI، میانگین متحرک) در اختیارت گذاشته می‌شه، "
        "تحلیلت رو بر همون اساس بده، نه بر اساس حدس. "
        "تحلیل بده نه پیش‌بینی قطعی، و در آخر یادآوری کن که توصیه‌ی مالی نیست."
    )

    for model_name in AI_MODELS_FALLBACK:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_prompt},
                    ],
                },
                timeout=30,
            )
            result = response.json()

            if "choices" in result:
                print(f"DEBUG - Used model: {model_name}")
                return result["choices"][0]["message"]["content"]
            else:
                print(f"DEBUG - Model {model_name} failed: {result}")
                continue

        except Exception as e:
            print(f"DEBUG - Model {model_name} error: {e}")
            continue

    return None

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    waiting_message = await update.message.reply_text("⏳ در حال تحلیل داده‌های بازار، چند لحظه صبر کن...")

    data = get_coin_analysis("bitcoin")

    if data:
        market_context = (
            f"داده‌های فعلی بیت‌کوین:\n"
            f"- قیمت: ${data['price']:,.2f}\n"
            f"- RSI (۱۴ روزه): {data['rsi']:.1f}\n"
            f"- میانگین متحرک ۷ روزه: ${data['sma_7']:,.2f}\n"
            f"- میانگین متحرک ۲۵ روزه: ${data['sma_25']:,.2f}\n\n"
        )
    else:
        market_context = "توجه: در حال حاضر دسترسی به داده‌های زنده‌ی بازار ممکن نیست.\n\n"

    full_prompt = f"{market_context}سوال کاربر: {user_message}"

    ai_reply = call_ai_model(full_prompt)

    await waiting_message.delete()

    if ai_reply:
       await update.message.reply_text(RTL_MARK + ai_reply)
    else:
        await update.message.reply_text("متأسفم، الان سرورهای AI شلوغن. لطفاً چند دقیقه دیگه دوباره امتحان کن.")


   
async def post_init(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_report, "cron", hour=9, minute=0, args=[app])
    scheduler.start()

 
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("analysis", analysis))
    app.add_handler(CommandHandler("setcoins", set_coins))
    app.add_handler(CommandHandler("mycoins", my_coins))
    app.add_handler(CallbackQueryHandler(button_handler))        
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_ai))

    print("Welcome back, boss! The bot is online and ready to roll.")
    app.run_polling()


if __name__ == "__main__":
    main()




    