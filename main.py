from sys import platform
from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy, run, gather
from datetime import datetime

from fake_useragent import UserAgent
from aiohttp_proxy import ProxyConnector
from aiohttp import ClientSession
from web3 import AsyncWeb3
from web3.middleware import async_geth_poa_middleware
from eth_account.messages  import encode_defunct


class Account:
    def __init__(
            self,
            private_key: dict,
            id: int
    ):  
        self.id = id
        self.private_key = private_key
        self.w3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider('https://mainnet.infura.io/v3/'),
            middlewares=[async_geth_poa_middleware]
        )
        self.address = self.w3.eth.account.from_key(private_key=self.private_key).address


    async def sign_message(self, message: str) -> None:
        message_to_sign = encode_defunct(text=message)
        self.signature = self.w3.eth.account.sign_message(message_to_sign, self.private_key).signature.hex()


    async def check_airdrop(self) -> int | None:
        ua = UserAgent(os=["windows"], browsers=['chrome'])
        proxy = f'{self.proxy[self.proxy.find(":")+6:]}@{self.proxy[:self.proxy.find(":")+5]}'

        async with ClientSession(connector=ProxyConnector.from_url(url="http://" + proxy), headers = {
            'user-agent': ua.random
            }) as client:

            response = await client.get(f'https://airdrop.zkfair.io/api/airdrop?address={self.address}&API-SIGNATURE={self.signature}&TIMESTAMP={self.timestamp}')

            data = (await response.json())['data']
            account_profit = data['account_profit']

            return round(int(account_profit) / 1e18, 2) if account_profit else None


async def start(privates: list[str, str]) -> None:
    tasks = []
    for id, key in enumerate(privates, start=1):
        tasks.append(main(id, key))
    
    await gather(*tasks)


async def main(id: int, key: str) -> None:
    account = Account(key, id)

    account.proxy = proxies[id-1]

    account.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'

    message = f'{account.timestamp}GET/api/airdrop?address={account.address}'

    await account.sign_message(message)
    print(id, account.address, await account.check_airdrop(), sep=' | ')


if __name__ == '__main__':
    if platform.startswith("win"):
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    with open('private_keys.txt') as file:
        privates = file.read().splitlines()

    with open('proxies.txt') as file:
        proxies = file.read().splitlines()
    
    run(start(privates))
