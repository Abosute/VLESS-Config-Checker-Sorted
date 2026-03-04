import httpx
import asyncio
import sys
from httpx import HTTPStatusError
from loguru import logger
from enum import Enum
from typing import Optional
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

    async def check_connection_from_list(self, links: list[str]) -> list[dict[str, int]]:
        if not links:
            return []

        promise = [self._check_connection(link) for link in links if link.startswith('vless://')]
        alive = []

        handler_id = logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")
        logger.remove(0) 

        try:
            with tqdm(total=len(promise), desc="🔍 Проверка", unit="cfg", colour="green") as pbar:
                for task in asyncio.as_completed(promise):
                    result = await task

                    if result['latency'] > 0:
                        logger.success(f"ЕСТЬ ЖИВОЙ: {result['latency']}ms")
                        alive.append(result)
                    else:
                        logger.info(f"Мертв: {result['latency']}")

                    pbar.update(1)
        finally:
            logger.remove(handler_id)
            logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

        return alive

    def write_alive_in_file(self, ping_list: list, name_file:str='best_cfg') -> None:
        self._check_exception(ping_list, list, True)
        self._check_exception(name_file, str, True)

        sorted_alive = sorted([link for link in ping_list if link['latency'] > 0], key=lambda link: link['latency'])

        with open(name_file + '.txt', 'w', encoding='UTF-8') as file:
            for link in sorted_alive:
                file.write(f"{link['link'].strip()}\n")

async def main():
    # Создаем экземпляр нашего комбайна
    # concurrent_limit=20, чтобы не вешать систему процессами xray
    pon = VlessPingAndSorted(concurrent_limit=20, timeout=10)

    # Список ссылок (можешь загрузить из файла)
    raw_links = ['vless://e9979910-79d1-4621-a93c-b2a579c44ba7@104.16.86.73:8880?path=%2FJ5aLQOY1R9ONWYCM%3Fed%3D2560&security=none&encryption=none&host=vngsupply.ip-ddns.com&type=ws#%F0%9F%87%B9%F0%9F%87%B4%40vpn_ioss%20%E2%99%BB%EF%B8%8F%20%D8%B9%D8%B6%D9%88%20%D8%B4%D9%88', 'vless://d5310380-e2eb-4593-bd40-2b5a09c56c1f@ve-sw.volnalink.uk:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=pingless.com&fp=qq&pbk=a3_DLO6p_ZfPf7I0JFTVlAI2pPAPtC-ji2diyPcHcQA&sid=7f892758&type=tcp#🇸🇪 Швеция VPN', 'vless://25efc727-e853-49ba-9609-3c20009d0e7a@104.18.13.229:2052?encryption=none&host=winbiss-0tpka6-v1.winbiss.workers.dev&path=/&security=none&type=ws#@AkbarConfig👈کانفیگ روزانه در', 'vless://be015dd2-30b4-4fcf-a9ee-080c13ac13fb@2.56.125.209:49868/?type=tcp&encryption=none&flow=&sni=yahoo.com&fp=chrome&security=reality&pbk=joEKL4Itljxodt1SOe1itSMrAH9bk_udpPtXgIjdu10&sid=6d638e#48%F0%9F%A6%96%40oneclickvpnkeys', 'vless://2271c50f-ac7a-4d7f-8b04-64085b0daa56@a.pabloping.cloud:2052?mode=auto&path=/pabloping/?TELEGRAM-YamYamProxy_YamYamProxy_YamYamProxy_YamYamProxy_YamYamProxy&security=none&encryption=none&host=nlbv2.pabloping.pro&type=xhttp#سرور رایگان متصل بیشتر در چنل🌊 @vmess_ir', 'vless://Telegram:@Free_VPN_CH@5.10.215.8:2096?path=/sg-lnd&security=tls&encryption=none&host=tn1rr.qzz.io&type=ws&sni=tn1rr.qzz.io#کانال تلگرام : Free_VPN_CH@', 'vless://0c950031-22e5-4476-a1e3-b20d089bd6a8@91.99.115.173:443?hiddify=1&sni=hostgator.com&type=tcp&alpn=http%2F1.1&host=hostgator.com&encryption=none&fp=chrome&headerType=none&flow=xtls-rprx-vision&security=reality&pbk=mEzwGx3LUXPR-sw8RFmlGM_ctzTwPlgq-mxku4wtBnc&sid=c1&headers=%7B%27User-Agent%27%3A%20%27Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F122.0.0.0%20Safari%2F537.36%27%2C%20%27Pragma%27%3A%20%27no-cache%27%7D#%F0%9F%9A%80%20%40V2rayMastermind', 'vless://1bed7f5e-3f85-45f2-a855-3b1fef63635b@usa122.luckerusa.org:444?mode=auto&path=/api/v1/&security=reality&encryption=none&pbk=BhTJ3phnq-Z-10aFKSsj1lzhA8mULR4L6leE4-0WTAs&fp=chrome&type=xhttp&sni=usa122.luckerusa.org#Telegram:@config_proxy 🔥', 'vless://05519058-d2ac-4f28-9e4a-2b2a1386749e@13.39.197.56:22224?type=ws&security=tls&path=/telegram-channel-vlessconfig&sni=trojan.burgerip.co.uk#@VlessConfig 🇨🇵', 'vless://e384913f-8863-47b4-8858-a84b68abb4a6@144.31.130.55:23335?encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk=7Gi8eiUU9TIVbGuvSU16gl5-Aqt7tcCSB9x6CSxyvik&security=reality&sid=67b1e94e4dd1ef90&sni=icloud.com&type=tcp#%3E%3E%40oneclickvpnkeys%3A%3APL', 'vless://16068e83-af4c-49ba-8048-98fcff3e5e7b@104.26.14.21:443?security=tls&encryption=none&sni=afrcloud22.mmv.kr&type=ws&host=afrcloud22.mmv.kr&path=/131.186.26.129=30443#@chillguy_vpn', 'vless://c8812004-f201-4c73-8f98-8b75f3f3ddb6@194.61.3.100:17799/?type=tcp&encryption=none&path=///AbriVPN--AbriVPN--AbriVPN--AbriVPN--AbriVPN--AbriVPN--AbriVPN--AbriVPN--AbriVPN--AbriVPN--AbriVPN---AbriVPN--AbriVPN--AbriVAbriVAbriVPN--AbriVPN--AbriVPN--AbriVPN--v&host=ripe.net&headerType=http&security=none#@AbriVPNbot-🇬🇧', 'vless://6202b230-417c-4d8e-b624-0f71afa9c75d@143.20.213.206:8443?path=/?ed&security=tls&encryption=none&host=sni.111000.indevs.in&fp=chrome&type=ws&sni=sni.111000.indevs.in#@Golestan_VPN 🆓 IRAN', 'vless://8feb77b2-c855-4aeb-8378-f93cf1985b9b@www.internetwebhub.blog:8880?encryption=none&host=mail.networkstreaming.fUN.&mode=auto&path=/Tel:@Ahmedhamoomi_Servers,Tel:@Ahmedhamoomi_Servers,Tel:@Ahmedhamoomi_Servers,Tel:@Ahmedhamoomi_Servers,Tel:@Ahmedhamoomi_Servers,Tel:@Ahmedhamoomi_Servers,Tel:@Ahmedhamoomi_Servers,Tel:@Ahmedhamoomi_Servers&security=none&type=xhttp#🇩🇪 Frankfurt : @Ahmedhamoomi_Servers', 'vless://47702dbb-6607-4d76-80e9-cd75327be3e7@162.159.38.76:443?allowInsecure=1&encryption=none&host=zrf-623.pages.dev&path=%2Fproxyip%3Dsjc.o00o.ooo%3A443&security=tls&sni=zrf-623.pages.dev&type=ws#%3E%3E%40oneclickvpnkeys%3A%3AUS', 'vless://f862698b-5c8a-4209-a961-ca6b2b9bf503@37.139.33.57:8443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=m.vk.ru&fp=chrome&pbk=_CjW0Khlrr5z5oc9Oy6-w2ZEanz-zMBktVn5EOX9oTM&sid=6419bed7fd0a2cff&type=tcp&headerType=none#https://t.me/allproconf', 'vless://10d7df50-b22d-406d-9e64-3e831fa0149e@3.127.211.41:44586/?type=tcp&encryption=none#🌐 TCP-None 📁 @Free_World2 (25)', 'vless://e9979910-79d1-4621-a93c-b2a579c44ba7@104.17.1.197:8880?path=%2FfgvtHUpS6R8Rv8s5%3Fed%3D2560&security=none&encryption=none&host=VngSuPpLY.IP-Ddns.com&type=ws#%F0%9F%87%B2%F0%9F%87%A9%40vpn_ioss%20%E2%99%BB%EF%B8%8F%20%D8%B9%D8%B6%D9%88%20%D8%B4%D9%88', 'vless://d7bbfe83-b037-48ae-996c-b98ed0441ba2@188.114.97.141:443?path=/Telegram-@proxy_mtm/?ed=2560&security=tls&encryption=none&host=e10c0e4b.oodaeq2.pages.dev&fp=chrome&type=ws&sni=e10c0e4b.oodaeq2.pages.dev#@torang_vpn', 'vless://b8773ac0-5d39-455d-a05b-a5f14d194049@65.109.221.182:46000?security=none&encryption=none&headerType=none&type=tcp#@Golestan_VPN - 🕊️', 'vless://faefbd75-9a1c-4bbf-9b90-816966ecf554@172.66.40.99:8880?path=/datax?ed=2560&security=none&encryption=none&host=amsterdam.11.v.www.speedtest.net.nestle.ir.ftp.debian.org.tmo.docb.datax.click.dataxshop.ir&type=httpupgrade#telegram : @datax_proxy', 'vless://76755143-35fc-4b1f-a793-3b24d31f4f6a@3.70.236.204:17373?security=none&encryption=none&headerType=none&type=tcp#⚡Telegram = @prrofile_purple', 'vless://fc4ec719-ce0a-3729-9d6f-ea5478e2765c@love-dnc.animallzoo-vip.pro:8443?mode=auto&path=/assets/css/style.css?ed=2080&security=tls&encryption=none&type=xhttp&sni=e9u8wghf97u.animallzoop.ir#🇳🇱MCI AZADIIIVPN', 'vless://c544111e-cb4d-48c1-b05e-1a7c4b0a5000@7fra.solonettochka.ru:443?security=reality&encryption=none&pbk=5Y8SmPZENDPp93lANbxf_sO7vKEFNIEqBNL6sx2vigI&headerType=none&fp=chrome&spx=/EytS2WsNGODUE1q&type=tcp&flow=xtls-rprx-vision&sni=www.google.com&sid=874e4e#@Golestan_VPN - All net', 'vless://9a39f63e-28c8-4560-af18-b01b9916ef1b@www.visa.com.sg:8443?path=Tel-proxy_mtm/%3Fed%3D2560&amp%3Bsecurity=tls&amp%3Bencryption=none&amp%3Bhost=pardazesh-tgws.pages.dev&amp%3Bfp=random&amp%3Btype=ws&amp%3Bsni=pardazesh-tgws.pages.dev#%F0%9F%87%BD%F0%9F%87%BD%20XX%20%7C%20VLESS%20%7C%20%40torang_vpn%20%231', 'vless://f8be92b6-b31f-4d8b-ba7d-20781595fa0e@194.87.80.9:8081?security=reality&encryption=none&pbk=nID_kfSoZPfWS1XZUT1dZnR2mwaoRtUROtBpmqCWEiQ&host=%2F%3FBIA_TELEGRAM%40MARAMBASHI_MARAMBASHI_MARAMBASHI&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=yahoo.com&sid=d0a3f84aabd21574#%40Daily_Configs`', 'vless://5dc15e15-f285-4a9d-959b-0e4fbdd77b63@162.159.45.153:443?allowInsecure=1&encryption=none&host=powered-by-surena.user68f797c2f3e1b.workers.dev&path=/&security=tls&sni=powered-by-surena.user68f797c2f3e1b.workers.dev&type=ws#🐻56@oneclickvpnkeys', 'vless://6202b230-417c-4d8e-b624-0f71afa9c75d@195.201.228.23:443?allowInsecure=1&encryption=none&host=sni.111000.v6.navy&path=%2F%3FTelegram%F0%9F%87%A8%F0%9F%87%B3%2B%40WangCai2%3D&security=tls&sni=sni.111000.v6.navy&type=ws#%3E%3E%40oneclickvpnkeys%3A%3ADE', 'vless://a4f7ac23-8146-464b-a932-9753f97303aa@sr-d-2.sedarchahar.top:9102?security=none&encryption=none&host=api.live98.ir&headerType=http&type=tcp#', 'vless://af07a5ea-e637-41bd-f88f-bc4493b645a2@18.197.25.140:32016?security=none&encryption=none&headerType=none&type=tcp#@MxV2ray', 'vless://ad8a28d6-a327-4ccc-9335-41fdd9738437@ip-data.turkserver.ir:2087?path=/&security=tls&encryption=none&insecure=0&host=all-fm2.netsnap.ir.&fp=chrome&type=ws&allowInsecure=0&sni=all-fm2.netsnap.ir.#@MxV2ray', 'vless://3f0f36f5-f091-45c5-88c9-4bcc545b922c@betty.ns.cloudflare.com:2096?path=/45.76.183.217=49292&security=tls&encryption=none&host=hetz.x-smm.com&fp=chrome&type=ws&sni=hetz.x-smm.com#🇩🇪 |⚡@EuServer', 'vless://59c0031e-6b09-4de2-ad03-83f0998a1f92@185.146.173.237:2095?path=/@Vpn_Mikey،@Vpn_Mikey&security=none&encryption=none&host=V2ray-_-_-_-_-Vpn_Mikey.Amir-Mikey.Tech.&type=ws#@Hope_Net-join-us-on-Telegram', 'vless://bdf97c06-ae1f-47e9-b47a-9d9ff47b5820@213.176.126.60:43800?security=none&encryption=none&host=skyroom.online&headerType=http&type=tcp#@v2rayland02🌐', 'vless://df0680ca-e43c-498d-ed86-8e196eedd012@95.164.45.85:8880?security=&encryption=none&type=grpc#v2raynplus |', 'vless://e384913f-8863-47b4-8858-a84b68abb4a6@2.cdnconn.com:23335?security=reality&encryption=none&pbk=7Gi8eiUU9TIVbGuvSU16gl5-Aqt7tcCSB9x6CSxyvik&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=icloud.com&sid=67b1e94e4dd1ef90#@vpnbaz 🧶', 'vless://3b7ec44b-66d8-4822-b772-f1f50c3fec95@ip-data.turkserver.ir:2083?path=/&amp%3Bsecurity=tls&amp%3Bencryption=none&amp%3Balpn=h2%2Chttp/1.1&amp%3Bhost=all-dm1.netsnap.ir.&amp%3Bfp=firefox&amp%3Btype=ws&amp%3Bsni=all-dm1.netsnap.ir.#%F0%9F%87%BD%F0%9F%87%BD%20XX%20%7C%20VLESS%20%7C%20%40red2ray%20%232', 'vless://90c7ad5e-cd15-4314-b39b-aeabd397d592@www.visa.com.sg:2087?path=%2F%3Fed%3D2560&security=tls&encryption=none&host=vl.hongkong6.qzz.io&fp=random&type=ws&sni=vl.hongkong6.qzz.io#%F0%9F%87%BA%F0%9F%87%BE%40vpn_ioss%20%E2%99%BB%EF%B8%8F%20%D8%B9%D8%B6%D9%88%20%D8%B4%D9%88', 'vless://e4824193-4f54-453b-d037-88368e85ef0e@185.236.232.189:8880?mode=gun&security=none&encryption=none&type=grpc#%F0%9F%87%BA%F0%9F%87%B8%F0%9F%A6%85%20United%20States', 'vless://e0c50817-86dd-4ee1-bca3-6e296d85dd59@chatgpt.com:2083?mode=multi&security=tls&encryption=none&insecure=0&fp=chrome&type=grpc&serviceName=Love&allowInsecure=0&sni=blouck-de.gozarcloud.ir#🚀 Telegram = @v2ray_configs_pools', 'vless://7553f8fe-2b75-4864-8717-00634a9e2e27@maxb08.ava-shop.ir:2096?security=reality&encryption=none&pbk=K0iITauuYEqIayR3IB5Ny8MVKyORDJ65rUSHc3tLe1E&headerType=none&fp=chrome&type=tcp&sni=play.google.com&sid=42c0b628ba6a42a9#@bored_vpn', 'vless://e4824193-4f54-453b-d037-88368e85ef0e@45.82.251.78:8880?mode=gun&security=none&encryption=none&authority=ZenixVPN_Channel&type=grpc#%40netmelli15', 'vless://67eef5b1-27ee-4ea2-bcf3-1d736711720c@trt.fastlynew.hosting-ip.com:80?mode=auto&path=/?ed=2560&security=none&encryption=none&host=maxfr219.global.ssl.fastly.net&type=xhttp#@V2rayNG3', 'vless://caedb6d9-aece-4e6a-9d6c-29f73df2f1a5@188.114.99.99:2053?type=grpc&serviceName=https://t.me/new_proxy_channel-@new_proxy_channel&authority=&security=tls&fp=chrome&alpn=http/1.1&sni=kanon.parhamtraberthos.IR.#VIP Channel-FREE CONFIG', 'vless://Parsashonam-301@185.146.173.39:8880?type=httpupgrade&path=%2FParsashonam-Parsashonam-Parsashonam%2F%3Fed%3D2056&host=De.Parsashonam.CfD.&security=none#@Parsashonam', 'vless://8dc7722c-2767-4eea-a28b-2f8daacc07e3@yesok42v2.ip4exordir.shop:8880?mode=gun&security=&encryption=none&type=grpc#%40Proxy_sh', 'vless://48ff2b70-e180-582f-8866-d9a2edeed5f5@57.129.53.181:23576?security=reality&encryption=none&pbk=1y5h2FGWKXTJ9xLPCqPo6Mw7RxoZzh6fGkEQKNxpZ3s&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=fuck.rkn&sid=01#🔵@chillguy_vpn', 'vless://19a1e5b1-6289-4fe6-9aad-be285510942d@5.255.100.32:8080/?encryption=none&flow=&host=check-host.net&type=tcp&headerType=http#%3E%3E%40v2ray_configs_pool%3A%3ANL', 'vless://4bc7d558-1943-44de-bd82-56920bc9383e@150.241.94.142:7443?encryption=none&fp=chrome&pbk=9Ow4bZxApNkRwAjQxyr_aZsBcJGc__jemUA7__BbZTE&security=reality&serviceName=vless&sid=ab1c1a11&sni=www.google.com&type=grpc#🐻54@oneclickvpnkeys', 'vless://910e3778-bbee-492b-a1e5-5f9c1cfe4194@85.133.250.87:41679?security=&encryption=none&host=78.157.49.67&headerType=http&type=tcp#1-a7r23858', 'vless://8242f0cf-a7af-40f0-bae0-ca1f1daa85a9@193.142.59.229:8443?encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&security=reality&sid=6ba85179e30d4fc2&sni=ign.dev&type=tcp#📀14@oneclickvpnkeys']

    print(f"🚀 Начинаю проверку {len(raw_links)} конфигов...")
    
    # Запускаем наш реактивный движок
    ASA = await pon.check_connection_from_list(raw_links)

    pon.write_alive_in_file(ASA)
    
    print("🏁 Проверка всех ссылок завершена.")

if __name__ == "__main__":
    asyncio.run(main())