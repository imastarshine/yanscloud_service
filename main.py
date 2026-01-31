import asyncio

import aiogram.utils.formatting
from aiogram.utils.formatting import Text, BlockQuote
from dotenv import load_dotenv
import yadisk
import os
import io

import src.sc
import src.db
import src.ydisk
import src.shared
import src.telegram
from src.logger import cleanup_old_logs, logger
# TODO: add logger


def lock_script():
    with open("app.lock", "w") as f:
        f.write("lock")


async def send_with(telegram: src.telegram.Telegram, message: Text | str):
    if telegram:
        await telegram.send_log(message)


async def main():
    cleanup_old_logs()

    telegram: src.telegram.Telegram = None

    if not src.shared.TELEGRAM_TOKEN or not src.shared.TELEGRAM_CHAT_ID:
        logger.warn("telegram bot is not setup")
    else:
        logger.info("creating telegram bot")
        try:
            telegram = src.telegram.Telegram()
            telegram._initialized = True
        except Exception as telegram_bot_create:
            logger.exception("failed to create telegram bot", exc_info=telegram_bot_create)
            telegram = None

    logger.info("initializing yandex disk")
    await src.ydisk.disk.init()

    disk_is_available = await src.ydisk.disk.check()
    if not disk_is_available:
        logger.critical("Yandex.Disk is not available. Locking script")
        await send_with(telegram, Text(
            BlockQuote("[yanscloud_service] 🚫"),
            BlockQuote("🖋️ | Yandex.Disk is not available. Locking script"),
        ))
        lock_script()
        exit(63)

    await src.ydisk.disk.create_folders()
    logger.info("yandex disk is available")
    logger.info("initializing soundcloud")

    try:
        await src.sc.soundcloud.init()
    except Exception as e:
        logger.critical("failed to init soundcloud. Locking script", exc_info=e)
        await send_with(telegram, Text(
            BlockQuote("[yanscloud_service] 🚫"),
            BlockQuote("🖋️ | SoundCloud failed to connect. Locking script"),
        ))
        lock_script()
        exit(62)

    await src.db.database.connect()
    await src.db.database.init()

    logger.info("starting main loop")
    loop_fails = 0

    while True:

        try:
            tracks = await src.sc.soundcloud.get_tracks()
            logger.info(f"found {len(tracks)} tracks")
            permalink_urls = [track.get("permalink_url") for track in tracks]
            db_tracks = await src.db.database.check_many(permalink_urls)
            logger.info(f"found {len(db_tracks)} tracks in db")
            new_tracks = [track for track in tracks if track.get("permalink_url") not in db_tracks]
            logger.info(f"found {len(new_tracks)} new tracks")

            for index, track in enumerate(new_tracks):
                permalink = track.get("permalink_url")

                # await send_with(telegram, Text(
                #     BlockQuote("[yanscloud_service] 🔎"),
                #     BlockQuote(f"🖋️ | Found new track ({index}/{len(new_tracks)})\n"
                #                f"🏷️ | {track.get('title')}\n"
                #                f"🔗 | {permalink}"),
                # ))

                if not permalink:
                    continue

                logger.info(f"downloading {permalink} | {index}/{len(new_tracks)}")
                file, path = await src.sc.soundcloud.download_track(permalink)

                if path is None:
                    logger.error(f"failed to download {permalink}. {path=}")
                    if path == "failed download":
                        path = "failed to download, maybe this track is geo blocked"
                    await send_with(telegram, Text(
                        BlockQuote("[yanscloud_service] ⚠️"),
                        BlockQuote(f"🖋️ | Failed to download track ({index}/{len(new_tracks)}). "
                                   f"This track will be ignored on next scanning\n"
                                   f"🏷️ | {track.get('title')}\n"
                                   f"🔗 | {permalink}\n"
                                   f"⚠️ | {path}")
                    ))
                    await src.db.database.add_music(permalink, is_failed=True)
                    continue

                logger.info(f"downloaded {permalink}. uploading")

                if not await src.ydisk.disk.check():
                    logger.critical("Yandex.Disk is not available. Locking script")
                    await send_with(telegram, Text(
                        BlockQuote("[yanscloud_service] 🚫"),
                        BlockQuote("🖋️ | Yandex.Disk is not available. Locking script"),
                    ))
                    lock_script()
                    exit(63)

                await src.ydisk.disk.upload(file, path)
                logger.info(f"uploaded {permalink} - {path}")

                await send_with(telegram, Text(
                    BlockQuote("[yanscloud_service] 📥"),
                    BlockQuote(f"🖋️ | Downloaded track ({index}/{len(new_tracks)})\n"
                               f"🏷️ | {track.get('title')}\n"
                               f"📁 | {path}\n"
                               f"🔗 | {permalink}"),
                ))

                await src.db.database.add_music(permalink)
                await asyncio.sleep(6)

            await asyncio.sleep(900)
        except Exception as e:
            loop_fails += 1
            logger.exception("an exception occurred on run loop", exc_info=e)
            if loop_fails > 15:
                if telegram:
                    await telegram.send_log(Text(
                        BlockQuote("[yanscloud_service] 😱"),
                        BlockQuote("🖋️ | An more than 15 times exception occurred on main loop. Locking script"),
                    ))
                lock_script()

            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
