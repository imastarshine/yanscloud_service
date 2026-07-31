import yadisk
from yadisk.sessions.async_httpx_session import AsyncHTTPXSession

import src.shared
import io

proxy_session = AsyncHTTPXSession(proxy=src.shared.YADISK_PROXY) if src.shared.YADISK_PROXY else None


class YDisk:
    def __init__(self):
        self.client: yadisk.AsyncClient | None = None

    async def init(self):
        self.client = yadisk.AsyncClient(
            token=src.shared.YADISK_TOKEN,
            session=proxy_session
        )

    async def check(self):
        return await self.client.check_token()

    async def create_folders(self):
        if not await self.client.exists("app:/soundcloud"):
            await self.client.mkdir("app:/soundcloud")

    async def upload(self, file: io.BytesIO, path: str):
        if not path.startswith("app:/"):
            raise Exception(f"Invalid path. Must start with app:/. Got: {path}")

        await self.client.upload(file, path)


disk = YDisk()
