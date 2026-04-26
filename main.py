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
from src.classes import ExitCode

PROVIDER = "SoundCloud"


def lock_script():
    with open("app.lock", "w") as f:
        f.write("lock")
    exit(ExitCode.LOCKED_NOW)


def check_lock():
    if os.path.exists("app.lock"):
        exit(ExitCode.ALREADY_LOCKED)


def truncate_filename(filename, max_length=150):
    # Yandex.Disk can't handle paths longer than ~255 characters
    if len(filename) <= max_length:
        return filename

    name, ext = os.path.splitext(filename)
    available_space = max_length - len(ext) - 3

    if available_space < 10:
        return filename[:max_length - len(ext)] + ext

    half = available_space // 2

    new_name = f"{name[:half]}...{name[-half:]}{ext}"

    return new_name


async def send_with(telegram: src.telegram.Telegram, message: Text | str):
    if telegram:
        await telegram.send_log(message)


async def yandex_disk_unavailable(telegram: src.telegram.Telegram):
    logger.critical("Yandex.Disk is not available. Locking script")
    await send_with(telegram, Text(
        BlockQuote("[yanscloud_service] 🚫"),
        BlockQuote("🖋️ | Yandex.Disk is not available. Locking script"),
    ))
    lock_script()


async def provider_unavailable(telegram: src.telegram.Telegram, provider="SoundCloud"):
    logger.critical(f"failed to init {provider.lower()}. Locking script")
    await send_with(telegram, Text(
        BlockQuote("[yanscloud_service] 🚫"),
        BlockQuote(f"🖋️ | {provider} failed to connect. Locking script"),
    ))
    lock_script()


async def main():
    check_lock()
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
    if not await src.ydisk.disk.check():
        await yandex_disk_unavailable(telegram)

    await src.ydisk.disk.create_folders()
    logger.info("yandex disk is available")
    logger.info("initializing soundcloud")

    try:
        await src.sc.soundcloud.init()
    except Exception as e:
        logger.critical(f"got an error when initializing {PROVIDER}{e}", exc_info=e)
        await provider_unavailable(telegram, PROVIDER)

    await src.db.database.connect()
    await src.db.database.init()

    logger.info("starting main loop")
    loop_fails = 0

    while True:

        try:
            # TODO: Add "Track" class and use it here
            tracks = await src.sc.soundcloud.get_tracks()
            logger.info(f"found {len(tracks)} tracks")
            permalink_urls = [track.get("permalink_url") for track in tracks]
            db_tracks = await src.db.database.check_many(permalink_urls)
            logger.info(f"found {len(db_tracks)} tracks in db")
            new_tracks = [track for track in tracks if track.get("permalink_url") not in db_tracks]
            logger.info(f"found {len(new_tracks)} new tracks")

            for index, track in enumerate(new_tracks):
                permalink = track.get("permalink_url")

                if not permalink:
                    continue

                logger.info(f"downloading {permalink} | {index + 1}/{len(new_tracks)}")
                file, path = await src.sc.soundcloud.download_track(permalink)

                if path is None or path == "failed download":
                    logger.error(f"failed to download {permalink}. {path=}")
                    if path == "failed download":
                        path = "failed to download, maybe this track is geo blocked"
                    await send_with(telegram, Text(
                        BlockQuote("[yanscloud_service] ⚠️"),
                        BlockQuote(f"🖋️ | Failed to download track ({index + 1}/{len(new_tracks)}). "
                                   f"This track will be ignored on next scanning\n"
                                   f"🏷️ | {track.get('title')}\n"
                                   f"🔗 | {permalink}\n"
                                   f"⚠️ | {path}")
                    ))
                    await src.db.database.add_music(permalink, is_failed=True)
                    continue

                logger.info(f"downloaded {permalink}. uploading to {path} ({type(file)})")

                if not await src.ydisk.disk.check():
                    await yandex_disk_unavailable(telegram)

                try:
                    if len(path) > 190:
                        filename = path.removeprefix("app:/soundcloud/")
                        new_filename = truncate_filename(filename, 160)
                        path = f"app:/soundcloud/{new_filename}"
                        logger.warning(f"path too long! Changed from '{filename}' -> '{new_filename}' for {permalink} and {track.get('title')}")
                    await src.ydisk.disk.upload(file, path)
                except yadisk.exceptions.PathExistsError:
                    pass
                logger.info(f"uploaded {permalink} - {path}")

                await send_with(telegram, Text(
                    BlockQuote("[yanscloud_service] 📥"),
                    BlockQuote(f"🖋️ | Downloaded track ({index}/{len(new_tracks)})\n"
                               f"🏷️ | {track.get('title')}\n"
                               f"📁 | {path}\n"
                               f"🔗 | {permalink}"),
                ))

                await src.db.database.add_music(permalink, track.get('title'), path.removeprefix("app:/soundcloud/"), False)
                await asyncio.sleep(6)

            await asyncio.sleep(900)
        except Exception as e:
            loop_fails += 1
            logger.exception("an exception occurred on run loop", exc_info=e)
            if loop_fails > 20:
                if telegram:
                    await telegram.send_log(Text(
                        BlockQuote("[yanscloud_service] 😱"),
                        BlockQuote("🖋️ | An more than 20 times exception occurred on main loop. Locking script"),
                    ))
                lock_script()

            await asyncio.sleep(25)

if __name__ == "__main__":
    asyncio.run(main())
