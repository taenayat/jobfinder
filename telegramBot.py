import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
from api_token import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from datetime import datetime
import random

from linkedin_v2 import LinkedIn
from data_storage import DataStorage

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

JOB_TIME_THRESHOLD = 900
JOB_REPEAT_INTERVAL = JOB_TIME_THRESHOLD + int(random.uniform(-10, 20))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html('Hi!')

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your Chat ID is: {chat_id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def get_new_jobs(context: ContextTypes.DEFAULT_TYPE) -> None:
    linkedin = LinkedIn('Data Scientist', 'Berlin Metropolitan Area', time_threshold=JOB_TIME_THRESHOLD)
    storage = DataStorage()
    storage.load_data()

    jobs = linkedin.get_jobs()
    if len(jobs) != 0:
        for job in jobs:
            message = f"{job['title']}\n{job['company']}\n{job['location']}\n{job['time_posted']}\n\n{job['link']}"
            await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            storage.add_job(
                timestamp=datetime.now(),
                job_title=job['title'],
                company=job['company'],
                location=job['location'],
                link=job['link']
            )
    linkedin.close_driver()
    logger.info('LinkedIn driver closed')
    storage.save_data()
    logger.info('Data saved to storage')




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
