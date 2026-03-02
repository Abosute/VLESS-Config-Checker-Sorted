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
    INCORRECT_TYPE = 'Inccorect type'



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

    async def _get_contents(self, client: httpx.AsyncClient) -> Optional[list[dict]]:
        try:
            response = await client.get(self.api_url)

            response.raise_for_status()

            return response.json()
        except HTTPStatusError as e:
            logger.error(LogMessage.HTTPERROR.value.format(e))
        except Exception as e:
            logger.error(LogMessage.UNEXPECTED.value.format(e))

    async def get_sorted_by(self, *, type_file: str | list="file", name_file: str | list='', client: Optional[httpx.AsyncClient]=None) -> list[str]:
        if not client:
            async with httpx.AsyncClient() as independent_client:
                files = await self._get_contents(independent_client)
        else:
            files = await self._get_contents(client=client)

        if not isinstance(type_file, (str, list)) or not isinstance(name_file, (str, list)):
            logger.error(LogMessage.INCORRECT_TYPE.value)
            return []

        if not files:
            logger.error(LogMessage.EMPTY_FILES.value)
            return []

        sorted_files = []

        for file in files:
            sorted_by_type: bool = type_file == file['type'] if isinstance(type_file, str) else file['type'] in type_file
            sorted_by_name: bool = name_file in file['name'] if isinstance(name_file, str) else file['name'] in name_file #if the name is a str, it is checked for inclusion

            if sorted_by_type and sorted_by_name:
                sorted_files.append(file['download_url'])

        return sorted_files
    
    async def download_contents(self, contents: list[str]) -> list[str]:
        if not isinstance(contents, list):
            logger.error(LogMessage.INCORRECT_TYPE.value)
            return []
        
        if not contents:
            logger.error(LogMessage.EMPTY_FILES.value)
            return []
        
        contents_list = []


'''        async with httpx.AsyncClient() as client:
            async for link in contents:
                try:
                    response = await client.get(link)

                    response.raise_for_status()

                    test = response.text

                    contents_list.append(test)
                except HTTPStatusError:
                    pass
                except Exception:
                    pass

            return contents_list'''
        




client = GitHubClient("https://github.com/Magerko/universal-media-downloader")

async def main():
    ddd = await client.get_sorted_by(name_file='.txt', type_file=['file'])
    print(ddd)

    ddddd = await client.download_contents(ddd)

    print(ddddd)

asyncio.run(main())