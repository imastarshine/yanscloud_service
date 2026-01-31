# yanscloud_service ☁️

[English version](README_EN.md)

* This project automatically downloads your music from Soundcloud to your Yandex Disk cloud storage.

The script monitors your Soundcloud account for new tracks. Once it finds a song that is not yet in the project's database, it downloads it and uploads it to your Yandex Disk.

Optionally, the project supports Telegram notifications to keep you informed about successful uploads or any errors that occur.

---

## Data Preparation 🛠️

To run the script, you need to collect several tokens and IDs.

### 1. Yandex Disk

Follow the link below, authorize access, and copy the provided `YADISK_TOKEN`:
[Get Yandex Disk Token (Click)](https://oauth.yandex.ru/authorize?response_type=token&client_id=18d5b110a4914b40a0dcd6ada14292ed)

### 2. Soundcloud (AUTH_TOKEN and CLIENT_ID)

To get these values, open Soundcloud in your browser and open the "Developer Tools" (Debugger/Network):

* **Windows/Linux:** `F12` or `Ctrl + Shift + I`
* **macOS:** `Cmd + Option + I`

**Instructions:**

1. Go to the **Network** tab.
2. Refresh the page and select any request.
3. Find the `Authorization` header. The value starting with `OAuth...` is your **AUTH_TOKEN**.
4. Type `client_id` in the search field within the Network tab. Copy the value of this parameter—this is your **CLIENT_ID**.

### 3. Telegram Bot

If you want to receive notifications via Telegram:

1. Message [@BotFather](https://t.me/BotFather) on Telegram.
2. Use the `/newbot` command and follow the instructions.
3. You will receive a token in the format `123456789:ABCdefGhIJKlmNoPQRstuVWxYz`.
4. Make sure to send `/start` to your new bot; otherwise, it won't be able to send you messages.

**How to get your TELEGRAM_CHAT_ID (User ID):**

* **Via a specialized bot:**
  Message the bot [@UserInfoToBot](https://www.google.com/search?q=https://t.me/UserInfoToBot). It will reply with your data. Use the number from the `Id: 0` line.
* **Via Telegram Desktop (Developer Mode):**
1. Go to **Settings** -> **Advanced**.
2. Click on "Advanced". The "Experimental settings" menu will appear at the bottom.
3. Enable: `Show Peer IDs in Profile`.
4. Now go to your own profile and copy your ID.



---

## Environment Setup ⚙️

The project uses a `.env` file to store sensitive data. First, create it based on the example.

**Terminal command:**

* **Linux / macOS:**
```bash
cp .env-example .env
```


* **Windows (PowerShell):**
```powershell
copy .env-example .env
```



### Filling out .env

Open the `.env` file with any text editor and insert your data:

```env
YADISK_TOKEN="your_yandex_token"
AUTH_TOKEN="OAuth your_soundcloud_token"
CLIENT_ID="your_soundcloud_client_id"
PROXY_URL="socks5h://user:pass@ip:port"
TELEGRAM_TOKEN="your_bot_token"
TELEGRAM_CHAT_ID=0
```

**Important Notes:**

* **Proxy:** Used exclusively for bypassing restrictions while downloading tracks. If you don't need a proxy, leave the string empty or keep it as is.
* **Telegram:** If you do not plan to use notifications, leave `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` as they are.

---

## Installation and Launch 🚀

The project uses **Poetry** for dependency management.

### 1. Installing Dependencies

Make sure you have Poetry installed, then run the following command in the project folder:

```bash
poetry install
```

### 2. Running the Script

The project must be launched specifically via the `launch.py` file. You can do this in two ways:

**Method 1 (via poetry environment):**

```bash
poetry run python launch.py
```

**Method 2 (activating the shell and running):**

* **Linux / macOS / Windows:**
```bash
poetry shell
python launch.py
```