import httpx
import asyncio
from loguru import logger
from enum import Enum
from idinahuichmo import V2RayProxy as BaseV2RayProxy #он меня зае**л
from tqdm import tqdm

NAME_FOR_BEST_CONFIGS = "best_proxies"

class LogMessage(Enum):
    SUCCESS = 'Success'
    INVALID_LINK = 'Invalid link'
    TYPE_ERROR = "The link must be a string"
    UNEXPECTED = "Unexpected error {}"
    HTTPERROR = 'HTTPStatusError {}'
    EMPTY_FILES = 'Empty files'

class VlessPingAndSorted:
    def __init__(self, concurrent_limit=50, timeout=10):
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self.timeout = timeout
        self.sni = ['x5.ru', 'yandex.ru', 'vk.com', 'mail.ru', 'ozon.ru', 'sberbank.ru']

    @staticmethod
    def _check_exception(obj, check_instance:type, check_empty: bool=None) -> None:
        if not isinstance(obj, check_instance):
            logger.error(LogMessage.TYPE_ERROR.value)
            raise TypeError
        
        if check_empty and not obj:
            logger.error(LogMessage.EMPTY_FILES.value)
            raise ValueError

    def sorted_vless_links(self, raw_links: list[str], *, white_list: bool=True) -> list[str]:
        if not isinstance(white_list, bool) or not isinstance(raw_links, list):
            logger.error(LogMessage.TYPE_ERROR.value)
            return []
        
        if not raw_links:
            logger.error(LogMessage.EMPTY_FILES.value)
            return []
        
        clean = [link for link in raw_links if link.startswith('vless://')]

        if white_list:
            return [
                link for link in clean 
                if 'security=reality' in link and any(inc in link for inc in self.sni)
            ]

        return clean
    
    async def _check_connection(self, link:str) -> dict[str, int]:
        async with self.semaphore:
            proxy=None
            try:
                proxy = BaseV2RayProxy(link)

                async with httpx.AsyncClient(proxy=proxy.http_proxy_url, timeout=self.timeout) as client:
                    start_time = asyncio.get_event_loop().time()

                    response = await client.get('http://cp.cloudflare.com/generate_204')
                    
                    if response.status_code == 204:
                        latency = int((asyncio.get_event_loop().time() - start_time) * 1000)

                        return {'link': link, 'latency': latency}
                    
                    return {'link': link, 'latency': -1}
            except Exception as e:
                return {'link': link, 'latency': -1}
            finally:
                if proxy:
                    proxy.stop()

    async def check_connection_from_list(self, links: list[str], max_alive:int=20) -> list[dict[str, int]]:
        if not links:
            return []

        promise = [self._check_connection(link) for link in links if link.startswith('vless://')]
        alive = []

        with tqdm(total=len(promise), desc="🔍 Проверено", unit="cfg", colour="green") as pbar:
            for task in asyncio.as_completed(promise):
                result = await task

                if result['latency'] > 0:
                    alive.append(result)

                if len(alive) >= max_alive:
                    logger.info("Набралось нужное кол-во")
                    task.cancel()
                    return alive

                pbar.update(1)

        logger.info(f"Живый: {len(alive)}")

        return alive

    def write_alive_in_file(self, ping_list: list, name_file:str='best_cfg') -> None:
        self._check_exception(ping_list, list, True)
        self._check_exception(name_file, str, True)

        sorted_alive = sorted([link for link in ping_list if link['latency'] > 0], key=lambda link: link['latency'])

        with open(name_file + '.txt', 'w', encoding='UTF-8') as file:
            for link in sorted_alive:
                file.write(f"{link['link'].strip()}\n")
