import io
import re
from urllib.parse import unquote

import aiohttp
import curl_cffi
import soundcloudpy
from bs4 import BeautifulSoup

from src.logger import logger
import src.shared

BASE_PAGE = "https://soundloadmate.com/enB13"


class SC:
    def __init__(self):
        self.session: aiohttp.ClientSession = None
        self.api: soundcloudpy.SoundcloudAsyncAPI = None
        self.me: dict = None

        self.download_session: aiohttp.ClientSession = None

    async def init(self):
        self.session = aiohttp.ClientSession()
        self.api = soundcloudpy.SoundcloudAsyncAPI(src.shared.AUTH_TOKEN, src.shared.CLIENT_ID, self.session)

        await self.api.login()

        self.me = await self.api.get_account_details()

        # if src.shared.PROXY_URL and src.shared.PROXY_URL.startswith("socks5://"):
        #     connector = ProxyConnector.from_url(src.shared.PROXY_URL, rdns=True)
        # else:
        #     logger.info(f"{sc_url} Continue without download proxy")
        #     connector = None

        if src.shared.PROXY_URL.startswith("socks5://") or src.shared.PROXY_URL.startswith("socks5h://"):
            proxies = {
                "http": src.shared.PROXY_URL,
                "https": src.shared.PROXY_URL
            }
            self.download_session = curl_cffi.AsyncSession(impersonate="chrome142", proxies=proxies)
        else:
            self.download_session = curl_cffi.AsyncSession(impersonate="chrome142")

    async def get_tracks(self) -> list[dict]:
        return [item async for item in self.api.get_track_details_liked(self.me["id"])]

    async def close(self):
        await self.session.close()
        self.session = None

    async def download_track(self, sc_url: str) -> tuple[io.BytesIO, str]:
        try:
            # step 1: Get token
            logger.info(f"{sc_url} | step 1 : getting token")
            r = await self.download_session.get(BASE_PAGE, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            form = soup.find('form', {'name': 'formurl'})

            hidden_input = form.find('input', {'type': 'hidden'})
            token_name = hidden_input.get('name')
            token_value = hidden_input.get('value')

            # step 2: Action POST
            logger.info(f"{sc_url} | step 2 : posting action")
            res_action = await self.download_session.post(
                "https://soundloadmate.com/action",
                data={'url': sc_url, token_name: token_value},
                headers={'Referer': BASE_PAGE}
            )

            action_data = res_action.json()
            inner_soup = BeautifulSoup(action_data['html'], 'html.parser')
            form_track = inner_soup.find('form', {'name': 'submitapurl'})

            payload = {
                'data': form_track.find('input', {'name': 'data'}).get('value'),
                'base': form_track.find('input', {'name': 'base'}).get('value'),
                'token': form_track.find('input', {'name': 'token'}).get('value')
            }

            # step 3: Track POST
            logger.info(f"{sc_url} | step 3 : posting track")
            res_track = await self.download_session.post(
                "https://soundloadmate.com/action/track",
                data=payload,
                headers={'Referer': BASE_PAGE}
            )

            track_data = res_track.json()

            if 'data' not in track_data:
                return None, "failed download"

            final_soup = BeautifulSoup(track_data['data'], 'html.parser')
            download_link = final_soup.find('a', string=re.compile("Download Mp3")).get('href')

            # step 4: Download file
            logger.info(f"{sc_url} | step 4 : downloading file")
            res_file = await self.download_session.get(download_link, timeout=60)
            file_content = res_file.content

            content_disp = res_file.headers.get('content-disposition')
            filename = unquote(re.findall('filename="(.+)"', content_disp)[0]) if content_disp else "track.mp3"
            filename = re.sub(r'[\\/*?:"<>|]', "", filename)
            filepath = f"app:/soundcloud/{filename}"

            file_io = io.BytesIO(file_content)
            file_io.name = filename
            file_io.seek(0)

            return file_io, filepath
        except Exception as e:
            logger.exception(f"exception on download {sc_url}", exc_info=e)
            return None, None


soundcloud = SC()
