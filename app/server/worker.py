import asyncio
import logging

# from apps.burn.worker import update_subtitle
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# import pytz
# irst_timezone = pytz.timezone("Asia/Tehran")
logging.getLogger("apscheduler").setLevel(logging.WARNING)


async def worker():
    # await update_subtitle()

    scheduler = AsyncIOScheduler()
    # scheduler.add_job(update_subtitle, "interval", seconds=Settings.worker_update_time)

    scheduler.start()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
