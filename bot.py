import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من بات تحلیل کریپتو هستم. 🤖\nهنوز در حال ساخته شدنم، ولی به زودی کامل می‌شم!"
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


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btc_price = get_btc_price()
    if btc_price is None:
        await update.message.reply_text("متأسفم، الان نتونستم قیمت رو بگیرم. لطفاً چند لحظه دیگه دوباره امتحان کن.")
    else:
        await update.message.reply_text(f"قیمت لحظه‌ای بیت‌کوین: ${btc_price:,}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    print("Welcome back, boss! The bot is online and ready to roll.")
    app.run_polling()


if __name__ == "__main__":
    main()


    