import aiogram
import src.shared

from aiogram.utils.formatting import Text


router = aiogram.Router()


class Telegram:
    def __init__(self):
        self.bot: aiogram.Bot = aiogram.Bot(src.shared.TELEGRAM_TOKEN)
        self.dp = aiogram.Dispatcher()
        self.dp.include_router(router)
        self._initialized = False

    async def send_log(self, message: Text | str):
        if not self._initialized:
            return

        if isinstance(message, str):
            await self.bot.send_sticker(
                src.shared.TELEGRAM_CHAT_ID,
                message
            )
        else:
            await self.bot.send_message(
                src.shared.TELEGRAM_CHAT_ID,
                **message.as_kwargs()
            )
