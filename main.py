import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "users.db"


# ── База данных ─────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_user(user_id: int, username: str = None, first_name: str = None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name))
        conn.commit()
    except Exception as e:
        logging.error(f"Ошибка сохранения пользователя: {e}")
    finally:
        conn.close()


def get_all_users() -> list[int]:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Ошибка чтения пользователей: {e}")
        return []
    finally:
        conn.close()


init_db()


# ── Хендлер /start ─────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    save_user(user.id, user.username, user.first_name)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ ДА, ХОЧУ",
                    url="https://t.me/sasha_teatr?text=Привет%2C%20я%20по%20поводу%20бесплатной%20голды.%20Что%20нужно%20сделать%3F"
                )
            ]
        ]
    )

    await message.answer(
        "Хочешь **бесплатно** забрать голду для Standoff 2? 🔥",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ── Эхо (можно убрать или оставить) ─────────────────────────────────────
@dp.message()
async def echo(message: Message):
    await message.answer("Напиши /start, чтобы начать заново")


# ── Рассылка каждые 3 часа ──────────────────────────────────────────────
async def broadcaster():
    await asyncio.sleep(30)
    text = (
        "Напоминание! 🔥\n\n"
        "БЫСТРЕЕ ПИШЕМ!\n"
        "Забери бесплатную голду для Standoff 2 прямо сейчас 👇"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ ДА, ХОЧУ ГОЛДУ",
                    url="https://t.me/sasha_teatr?text=Привет%2C%20я%20по%20поводу%20бесплатной%20голды.%20Что%20нужно%20сделать%3F"
                )
            ]
        ]
    )

    while True:
        users = get_all_users()
        logging.info(f"Рассылка → найдено {len(users)} пользователей")
        sent_count = 0
        blocked_count = 0

        for user_id in users:
            try:
                await bot.send_message(
                    user_id,
                    text,
                    reply_markup=keyboard,
                    disable_notification=True
                )
                sent_count += 1
                await asyncio.sleep(0.07)
            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["blocked", "forbidden", "chat not found"]):
                    blocked_count += 1
                else:
                    logging.warning(f"Не удалось отправить {user_id}: {e}")

        logging.info(f"Рассылка завершена: отправлено {sent_count}, ошибок {blocked_count}")
        await asyncio.sleep(10800)  # 3 часа


# ── Запуск бота ───────────────────────────────────────────────────────
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(broadcaster())
    logging.info("Бот запущен • Standoff 2 голда")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())