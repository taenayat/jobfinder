import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
# from api_token import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from datetime import datetime
import random
import os
from dotenv import load_dotenv
import json

from linkedin import LinkedIn
from data_storage import DataStorage

JOB_TIME_THRESHOLD = 900
JOB_REPEAT_INTERVAL = JOB_TIME_THRESHOLD + int(random.uniform(-10, 20))
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
JOB_TITLE = "Data Scientist"
LOCATION = "Berlin Metropolitan Area"

# Configure logging with file handler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler('telegramBot.log'),
        logging.StreamHandler()
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html('Hi!')

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your Chat ID is: {chat_id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def get_new_jobs(context: ContextTypes.DEFAULT_TYPE) -> None:
    linkedin = LinkedIn(JOB_TITLE, LOCATION, time_threshold=JOB_TIME_THRESHOLD)
    logger.info('LinkedIn driver initialized')

    storage = DataStorage(
        use_csv=True,
        use_google_sheets=True,
        credentials_info=json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON')),
        spreadsheet_id=os.getenv('SPREADSHEET_ID'),
        worksheet_name=os.getenv('WORKSHEET_NAME')
    )

    jobs = linkedin.get_jobs()
    if len(jobs) != 0:
        for job in jobs:
            message = (
                f"✨ <b>{job['title']}</b>\n"
                f"🏢 <i>{job['company']}</i>\n"
                f"📍 {job['location']}\n"
                f"🕒 Posted: {job['time_posted']}\n"
                f"\n🔗 <a href=\"{job['link']}\">View Job</a>"
            )
            await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
            
            job_list = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                job['title'],
                job['company'],
                job['location'],
                job['link']
            ]
            storage.save_job(job_list)
            logger.info(f"Job saved: {job['title']} at {job['company']}")
            
    linkedin.close_driver()
    logger.info('LinkedIn driver closed')


def main() -> None:
    """Start the bot."""
    job_queue = JobQueue()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("getid", get_id))

    application.job_queue.run_repeating(get_new_jobs, interval=JOB_REPEAT_INTERVAL, first=2) # interval in seconds
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
