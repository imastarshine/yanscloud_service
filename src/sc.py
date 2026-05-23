import asyncio
import io
import random
import re
from urllib.parse import unquote

import aiohttp
import curl_cffi
import soundcloudpy
from bs4 import BeautifulSoup
from curl_cffi.requests.exceptions import RequestException
from curl_cffi.requests import Response

from src.logger import logger
import src.shared

BASE_PAGE = "https://soundloadmate.com/enB13"


def clamp(value: int, min_val: int, max_val: int):
    return max(min_val, min(value, max_val))


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

        if src.shared.PROXY_URL.startswith("socks5://") or src.shared.PROXY_URL.startswith("socks5h://"):
            proxies = {
                "http": src.shared.PROXY_URL,
                "https": src.shared.PROXY_URL
            }
            self.download_session = curl_cffi.AsyncSession(impersonate="chrome", proxies=proxies, timeout=src.shared.DOWNLOAD_TIMEOUT)
        else:
            self.download_session = curl_cffi.AsyncSession(impersonate="chrome", timeout=src.shared.DOWNLOAD_TIMEOUT)

    async def get_tracks(self) -> list[dict]:
        return [item async for item in self.api.get_track_details_liked(self.me["id"])]

    async def close(self):
        await self.session.close()
        self.session = None

    async def _retry_get(self, url: str) -> Response | None:
        for attempt in range(clamp(src.shared.DOWNLOAD_TIMEOUT_RETRY, 1, 100)):
            try:
                logger.info(f"trying to get {url} with {attempt} attempt")
                res_file: Response = await self.download_session.get(url)
                if res_file.status_code not in [200, 201, 202, 203, 204, 205, 206]:
                    logger.error(f"got {res_file.status_code} when downloading file from {url}")
                    await asyncio.sleep(random.uniform(4, 8))
                    continue
                return res_file
            except RequestException as e:
                error_msg = str(e)
                if getattr(e, "code", None) == 28 or "curl: (28)" in error_msg or "ErrCode: 28" in error_msg:
                    logger.error(f"received timeout ({e}) for {url} on {attempt} attempt")
                else:
                    logger.exception(f"something went wrong on downloading {url}", exc_info=e)
                await asyncio.sleep(random.uniform(15, 30))
            except KeyboardInterrupt:
                return None
            except SystemExit:
                return None
            except Exception as e:
                logger.exception(f"received {e} on {attempt} for {url}", exc_info=e)
                await asyncio.sleep(random.uniform(4, 8))

    async def download_track(self, sc_url: str) -> tuple[io.BytesIO, str]:
        try:
            # step 1: Get token
            logger.info(f"{sc_url} | step 1 : getting token")
            r = await self.download_session.get(BASE_PAGE, timeout=45)
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
                headers={'Referer': BASE_PAGE},
                timeout=45
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
                headers={'Referer': BASE_PAGE},
                timeout=45
            )

            track_data = res_track.json()

            if 'data' not in track_data:
                return None, "failed download"

            final_soup = BeautifulSoup(track_data['data'], 'html.parser')
            download_link = final_soup.find('a', string=re.compile("Download Mp3")).get('href')

            # step 4: Download file
            logger.info(f"{sc_url} | step 4 : downloading file")
            res_file = await self._retry_get(download_link)
            if not res_file:
                return None, "failed download"
            file_content = res_file.content

            content_disp = res_file.headers.get('content-disposition')
            filename = unquote(re.findall('filename="(.+)"', content_disp)[0]) if content_disp else "track.mp3"
            filename = re.sub(r'[\\/*?:"<>|]', "", filename)
            filepath = f"app:/soundcloud/{filename}"

            file_io = io.BytesIO(file_content)
            file_io.name = filename
            file_io.seek(0)

            return file_io, filepath
        except KeyboardInterrupt:
            return None, None
        except SystemExit:
            return None, None
        except Exception as e:
            logger.exception(f"exception on download {sc_url}", exc_info=e)
            return None, None


soundcloud = SC()
