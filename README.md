# 🤖 Crypto Analysis Bot

A Telegram bot that provides real-time cryptocurrency market analysis, combining technical indicators with AI-powered insights.

## 🛠️ Tech Stack

- 🐍 Python
- 🤖 Telegram Bot API
- 📊 pandas-ta
- 🪙 CoinGecko API
- 🧠 AI Models
- 🗄️ SQLite

## Tech Stack

- **Language:** Python 3.13
- **Bot Framework:** [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- **Market Data:** [CoinGecko API](https://www.coingecko.com/en/api)
- **Technical Analysis:** pandas, pandas-ta
- **AI:** OpenRouter (multi-model fallback system)
- **Database:** SQLite
- **Scheduling:** APScheduler
- **Deployment:** Railway

## Commands

| Command | Description |
|---|---|
| `/start` | Register and see welcome message |
| `/price` | Get current Bitcoin price |
| `/analysis [coin]` | Get technical analysis for a coin (default: BTC) |
| `/setcoins [coins]` | Set your favorite coins for daily reports |
| `/mycoins` | View your currently tracked coins |
| *(any message)* | Chat freely with the AI about market conditions |

## How It Works

1. The bot fetches live 30-day price history from CoinGecko
2. Technical indicators (RSI, moving averages) are computed using `pandas-ta`
3. For AI chat, real market data is injected into the prompt so responses are grounded in actual numbers, not guesses
4. If the primary AI model is unavailable, the bot automatically falls back to alternative models
5. A background scheduler sends daily market summaries to users based on their saved preferences

## Setup

1. Clone this repository
2. Create a virtual environment and install dependencies:
3. Create a `.env` file with:
4. Run the bot:

## Disclaimer

This bot provides technical analysis based on historical data. It does not provide financial advice or price predictions. All analysis includes appropriate disclaimers, and users are encouraged to do their own research before making financial decisions.

## Author

Built by [Amir](https://github.com/the4mir) as a portfolio project.
