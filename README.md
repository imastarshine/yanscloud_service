# yanscloud_service ☁️

[English version](README_EN.md)

* Это проект для автоматического скачивания вашей музыки из Soundcloud на ваш Яндекс.Диск.

Скрипт мониторит ваш аккаунт Soundcloud на наличие новых треков. Как только появляется песня, которой еще нет в базе данных проекта, он скачивает её и загружает на ваш Яндекс.Диск.

Опционально проект поддерживает уведомления в Telegram, чтобы вы всегда были в курсе успешных загрузок или возникших ошибок.

---

## Подготовка данных 🛠️

Для работы скрипта необходимо собрать токены.

### 1. Яндекс.Диск

Перейдите по ссылке ниже, подтвердите доступ и скопируйте полученный `YADISK_TOKEN`:
[Получить токен Яндекс.Диска (ТЫК)](https://oauth.yandex.ru/authorize?response_type=token&client_id=18d5b110a4914b40a0dcd6ada14292ed)

### 2. Soundcloud (AUTH_TOKEN и CLIENT_ID)

Чтобы получить эти данные, откройте Soundcloud в браузере и вызовите «Инструменты разработчика» (Debugger/Network):

* **Windows/Linux:** `F12` или `Ctrl + Shift + I`
* **macOS:** `Cmd + Option + I`

**Инструкция:**

1. Перейдите на вкладку **Network** (Сеть).
2. Обновите страницу и выберите любой запрос.
3. Найдите заголовок `Authorization`. Значение, начинающееся с `OAuth...` — это ваш **AUTH_TOKEN**.
4. В поле поиска во вкладке Network введите `client_id`. Скопируйте значение этого параметра — это ваш **CLIENT_ID**.

### 3. Telegram бот

Если вы хотите получать уведомления через телеграм то:

1. Напишите боту [@BotFather](https://t.me/BotFather) в Telegram.
2. Используйте команду `/newbot` и следуйте инструкциям.
3. Вы получите токен в формате `123456789:ABCdefGhIJKlmNoPQRstuVWxYz`.
4. Не забудьте отправить боту `/start` иначе он не сможет отправлять вам сообщения.

**Как получить ваш TELEGRAM_CHAT_ID (User ID):**

* **Через специального бота:**
Напишите боту [@UserInfoToBot](https://www.google.com/search?q=https://t.me/UserInfoToBot). В ответ он пришлет сообщение с вашими данными. Используйте число из строки `Id: 0`.
* **Через Telegram Desktop (Режим разработчика):**
1. Зайдите в **Настройки** -> **Продвинутые настройки**.
2. Нажмите на «Продвинутые настройки». Внизу появится пункт «Экспериментальные настройки».
3. Включаем: `Show Peer IDs in Profile`
4. Теперь перейдите в свой профиль. И скопируйте ваш ID.

---

## Настройка окружения ⚙️

Проект использует файл `.env` для хранения конфиденциальных данных. Сначала создайте его на основе примера.

**Команда для терминала:**

* **Linux / macOS:**
```bash
cp .env-example .env
```


* **Windows (PowerShell):**
```powershell
copy .env-example .env
```

### Заполнение .env

Откройте файл `.env` любым текстовым редактором и вставьте ваши данные:

```env
YADISK_TOKEN="ваш_токен_яндекса"
AUTH_TOKEN="OAuth ваш_токен_soundcloud"
CLIENT_ID="ваш_client_id_soundcloud"
PROXY_URL="socks5h://user:pass@ip:port"
TELEGRAM_TOKEN="ваш_токен_бота"
TELEGRAM_CHAT_ID=0
```

**Важные примечания:**

* **Прокси:** Используется исключительно для обхода ограничений при скачивании треков. Если прокси вам не нужен, просто оставьте строку пустой или не меняйте её.
* **Telegram:** Если вы не планируете использовать уведомления, оставьте `TELEGRAM_TOKEN` и `TELEGRAM_CHAT_ID` как есть.

---

## Установка и запуск 🚀

Для управления зависимостями в проекте используется **Poetry**.

### 1. Установка зависимостей

Убедитесь, что у вас установлен Poetry, и выполните команду в папке проекта:

```bash
poetry install
```

### 2. Запуск скрипта

Запуск проекта осуществляется строго через файл `main.py`. Вы можете сделать это двумя способами:

**Способ 1 (через окружение poetry):**

```bash
poetry run python main.py
```

**Способ 2 (активация оболочки и запуск):**

* **Linux / macOS / Windows:**
```bash
poetry shell
python main.py
```

### 3. Автозапуск скрипта

1. **Создайте файл службы:**
```bash
sudo nano /etc/systemd/system/yanscloud.service
```

2. **Вставьте следующее содержимое:**
   *(Замените `<USER>` на ваше имя пользователя, а `<PATH>` на полный путь к папке проекта)*
```ini
[Unit]
Description=Yanscloud Service
After=network.target
StartLimitIntervalSec=360
StartLimitBurst=5

[Service]
Type=simple
User=<USER>
WorkingDirectory=<PATH>
# Убедитесь, что путь к venv и main.py указан верно
ExecStart=<PATH>/.venv/bin/python <PATH>/main.py
Restart=on-failure
RestartSec=60
RestartPreventExitStatus=45 46 47 48

[Install]
WantedBy=multi-user.target
```

3. **Настройка прав доступа (пропустите, если используете root):**
```bash
# Замените <USER> и <PATH> на ваши значения
sudo chown -R <USER>:<USER> <PATH>
```

4. **Активация службы:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable yanscloud.service
sudo systemctl start yanscloud.service

# Просмотр логов в реальном времени:
sudo journalctl -u yanscloud.service -f -e
```
