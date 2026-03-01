import httpx
import asyncio
from httpx import HTTPStatusError
from loguru import logger
from enum import Enum
from typing import Optional

class LogMessage(Enum):
    SUCCESS = 'Success'
    INVALID_LINK = 'Invalid link'
    TYPE_ERROR = "The link must be a string"
    UNEXPECTED = "Unexpected error {}"
    HTTPERROR = 'HTTPStatusError {}'
    EMPTY_FILES = 'Empty files'

class GitHubClient:
    def __init__(self, url: str):
        self.api_url = url

    @property
    def api_url(self) -> str:
        return self._api_url

    @api_url.setter
    def api_url(self, new_url: str):
        self._raw_url = new_url
        if not isinstance(new_url, str):
            logger.error(LogMessage.TYPE_ERROR.value)
            self._api_url = ""
            return

        url = new_url.replace("github.com/", "api.github.com/repos/")

        if url.startswith("https://api.github.com/"):
            self._api_url = url + "/contents/"
        else:
            self._api_url = ""
            logger.error(LogMessage.INVALID_LINK.value)

    async def _get_contents(self) -> Optional[list[dict]]:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.get(self.api_url)

                response.raise_for_status()

                return response.json()
        except HTTPStatusError as e:
            logger.error(LogMessage.HTTPERROR.value.format(e))
        except Exception as e:
            logger.error(LogMessage.UNEXPECTED.value.format(e))

    async def get_sorted_by(self, *, type_file: str="file", in_name: str='') -> Optional[list]:
        files = await self._get_contents()

        if not files:
            logger.error(LogMessage.EMPTY_FILES.value)
            return []

        sorted_files = []

        for file in files:
            sorted_by_type = type_file == file['type']
            sorted_by_name = in_name in file['name']
            if sorted_by_type and sorted_by_name:
                sorted_files.append(file['download_url'])

        return sorted_files

client = GitHubClient("https://github.com/Magerko/universal-media-downloader")

async def main():
    ddd = await client.get_sorted_by(in_name=".txt")
    print(ddd)


asyncio.run(main())