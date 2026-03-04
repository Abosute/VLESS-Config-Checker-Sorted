import asyncio
from loguru import logger
from enum import Enum
from githubclient import GitHubClient
from VLESSparser import VlessPingAndSorted

class LogMessage(Enum):
    SUCCESS = 'Success'
    INVALID_LINK = 'Invalid link'
    TYPE_ERROR = "The link must be a string"
    UNEXPECTED = "Unexpected error {}"
    HTTPERROR = 'HTTPStatusError {}'
    EMPTY_FILES = 'Empty files'
    INCORRECT_TYPE = 'Inccorect type'

URL_BASE = [
    'https://github.com/barry-far/V2ray-Config',
    'https://github.com/igareck/vpn-configs-for-russia',
    'https://github.com/Epodonios/v2ray-configs',
    'https://github.com/kort0881/vpn-vless-configs-russia'
]

client = GitHubClient('https://github.com/igareck/vpn-configs-for-russia')
vless = VlessPingAndSorted()

async def main():
    y_menya_net_fantasii_list = await client.get_sorted_by(type_file="file", name_file=".txt")

    penis = await client.download_contents(y_menya_net_fantasii_list)

    chlen = list(set(vless.sorted_vless_links(penis)))

    eba = await vless.check_connection_from_list(chlen, max_alive=100)

    vless.write_alive_in_file(eba)



if __name__ == '__main__':
    asyncio.run(main())