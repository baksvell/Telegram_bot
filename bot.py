import os
import psycopg2
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение переменных окружения
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


def update_database(user_id: int, username: str) -> bool:
    try:
        # Подключение к базе данных PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )

        # Создание объекта курсора для выполнения SQL-запросов
        cursor = conn.cursor()
        # SQL-запрос для вставки или обновления записи
        cursor.execute(
            "INSERT INTO users (id, username) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username",
            (user_id, username)
        )

        # Применение изменений в базе данных
        conn.commit()

        # Закрытие курсора и соединения
        cursor.close()
        conn.close()

        # Логирование успешного обновления базы данных
        logger.info(f"User {user_id} ({username}) inserted/updated in the database.")

        return True

    except Exception as e:
        # Обработка ошибок при обновлении базы данных
        logger.error(f"Error updating database: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    logger.info(f"Received /start command from {user_id} ({username})")

    if update_database(user_id, username):
        logger.info("Attempting to send a welcome message.")
        try:
            await update.message.reply_text('Hello! Your data has been updated in the database.')
            logger.info("Welcome message sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
    else:
        logger.info("Attempting to send a failure message.")
        try:
            await update.message.reply_text('Failed to update your data in the database.')
            logger.info("Failure message sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send failure message: {e}")


# Запуск вашего Telegram-бота с использованием токена из файла .env
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    app.run_polling()
