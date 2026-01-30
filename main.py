import asyncio

from dotenv import load_dotenv
import yadisk
import os
import io

import src.sc
import src.db
import src.ydisk
# TODO: add logger


async def main():
    await src.ydisk.disk.init()

    disk_is_available = await src.ydisk.disk.check()
    if not disk_is_available:
        print("Y.Disk is not available! Maybe token is invalid?")
        exit(63)

    await src.ydisk.disk.create_folders()
    print("Y.Disk is available!")

    try:
        await src.sc.soundcloud.init()
    except Exception as e:
        print("SoundCloud is not available! Maybe client_id or oauth_token is invalid? or proxy is invalid?\n", e)
        exit(62)

    await src.db.database.connect()
    await src.db.database.init()

    print("All is OK!")
    print("Starting...")

    tracks = await src.sc.soundcloud.get_tracks()
    permalink_urls = [track.get("permalink_url") for track in tracks]
    db_tracks = await src.db.database.check_many(permalink_urls)
    new_tracks = [track for track in tracks if track.get("permalink_url") not in db_tracks]

    for index, track in enumerate(new_tracks):
        permalink = track.get("permalink_url")
        if permalink in db_tracks:
            print(f"Skip: {permalink} - already exists!")
            continue

        if not permalink:
            continue

        print(f"Downloading: {permalink} | {index}/{len(new_tracks)}")
        file, path = await src.sc.soundcloud.download_track(permalink)

        if path is None:
            print(f"Something went wrong with {permalink}!")
            continue

        print(f"Downloaded: {permalink} - {path}")
        print("Uploading...")

        if not await src.ydisk.disk.check():
            # TODO: more normal log
            print("Y.Disk is not available! Maybe token is invalid? (2)")
            exit(63)

        await src.ydisk.disk.upload(file, path)
        print("Uploaded! Adding to db...")

        await src.db.database.add_music(permalink)
        print("Sleeping...")

        await asyncio.sleep(6)


if __name__ == "__main__":
    asyncio.run(main())

# TOKEN = os.getenv("YADISK_TOKEN")
#
# if not TOKEN:
#     print("TOKEN is None!")
#     exit(1)
#
# disk = yadisk.YaDisk(token=TOKEN)
#
# if disk.check_token():
#     print("Good")
#     buffer = io.BytesIO()
#     buffer.write("Test file!".encode("utf-8"))
#     buffer.seek(0)
#     disk.upload(buffer, "app:/test.txt")
# else:
#     print("Token is invalid.")
