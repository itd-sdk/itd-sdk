from os import getenv

import pytest
from dotenv import load_dotenv

from itd import ITDClient, ITDConfig
from itd.enums import RateLimitMode
from itd.post import Post


load_dotenv()
config = ITDConfig(RateLimitMode.NO)

@pytest.fixture(scope="session")
def client():
    token = getenv('TOKEN')
    if not token:
        pytest.skip('TOKEN not set in .env')
    return ITDClient(token, config=config)


@pytest.fixture(scope="session")
def client2(client):
    token = getenv('TOKEN_2')
    if not token:
        pytest.skip('TOKEN_2 not set in .env')
    return ITDClient(token, config=config)


@pytest.fixture(scope="session")
def client_sub(client):
    token = getenv('TOKEN_SUB')
    if not token:
        pytest.skip('TOKEN_SUB not set in .env')
    return ITDClient(token, config=config)


@pytest.fixture(scope="session")
def redis_post(client): # думаешь redis это какое нибудь заумное важное название? а нет, это просто редис зплвца
    return Post('1cbe5926-2d08-4e17-879d-7732b94ed354')
