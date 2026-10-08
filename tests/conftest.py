import pytest
from dotenv import load_dotenv
from helpers import make_response, make_token

from itd import ITDConfig, init_client
from itd.models.post import Post

load_dotenv()
config = ITDConfig()


@pytest.fixture(scope='session')
def client():
    return init_client(config=config)


@pytest.fixture(scope='session')
def client2(client):
    return init_client('test_2', config=config, initial_refresh='')


@pytest.fixture(scope='session')
def client_sub(client):
    return init_client('test_3', config=config, initial_refresh='')


@pytest.fixture(scope='session')
def redis_post(client):  # думаешь redis это какое нибудь заумное важное название? а нет, это просто редис зплвца
    return Post('1cbe5926-2d08-4e17-879d-7732b94ed354')


# фикстуры для оффлайн тестов (test_auth, test_endpoint, test_errors)


@pytest.fixture
def keep_default_client():
    """Клиенты оффлайн тестов не должны становиться дефолтными для остальных"""
    from itd.core import default

    previous = default._default_client
    yield
    default._default_client = previous


@pytest.fixture
def fetches(monkeypatch):
    """Перехватить запросы вместо отправки"""
    calls = []

    def fake_fetch(client, method, url, params={}, files={}, sse=False):
        calls.append({'method': method, 'url': url, 'params': params, 'files': files})
        return make_response(200, {'data': {}})

    monkeypatch.setattr('itd.core.client.fetch', fake_fetch)
    return calls


@pytest.fixture
def refreshes(monkeypatch):
    """Перехватить обновление токена вместо запроса в v1/auth/refresh"""
    calls = []

    def fake_refresh_token(client):
        calls.append(client._profile.access)
        return make_response(200, {'accessToken': make_token(900)})

    monkeypatch.setattr('itd.core.client.refresh_token', fake_refresh_token)
    return calls
