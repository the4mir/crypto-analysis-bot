import sqlite3

DB_NAME = "bot_data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            favorite_coins TEXT DEFAULT 'btc'
        )
    """)
    conn.commit()
    conn.close()


def add_user_if_not_exists(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
    existing = cursor.fetchone()
    if not existing:
        cursor.execute("INSERT INTO users (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    conn.close()


def get_favorite_coins(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT favorite_coins FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0].split(",")
    return ["btc"]


def set_favorite_coins(chat_id, coins_list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    coins_str = ",".join(coins_list)
    cursor.execute(
        "UPDATE users SET favorite_coins = ? WHERE chat_id = ?",
        (coins_str, chat_id)
    )
    conn.commit()
    conn.close()