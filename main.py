from dotenv import load_dotenv
import yadisk
import os
import io

load_dotenv()
TOKEN = os.getenv("YADISK_TOKEN")

if not TOKEN:
    print("TOKEN is None!")
    exit(1)

disk = yadisk.YaDisk(token=TOKEN)

if disk.check_token():
    print("Good")
    buffer = io.BytesIO()
    buffer.write("Test file!".encode("utf-8"))
    buffer.seek(0)
    disk.upload(buffer, "app:/test.txt")
else:
    print("Token is invalid.")

