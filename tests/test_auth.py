from logging import WARNING, getLogger

import pytest
from helpers import make_client, make_response, make_token

from itd.core.client import Client
from itd.enums import AuthLevel
from itd.exceptions import AccessTokenExpiredError
from itd.core.request import api_wrapper

pytestmark = pytest.mark.usefixtures('keep_default_client')


def test_access_token_expiry():
    assert make_client(make_token(-10))._profile.access_data.is_expired
    assert make_client(make_token(30))._profile.access_data.is_expired  # истекает раньше, чем запас в минуту
    assert not make_client(make_token(900))._profile.access_data.is_expired
    assert make_client(None)._profile.access_data is None


def test_public_endpoint_does_not_refresh_token(fetches, refreshes):
    """Запросы без авторизации (search, hashtags, profile) не обновляют токен заранее - протухший перевыпустит api_wrapper по ответу сервера"""
    client = make_client(make_token(-10))

    client.request('get', 'search', {'q': 'итд'}, level=AuthLevel.NO)

    assert refreshes == []
    assert len(fetches) == 1


def test_endpoint_with_auth_refreshes_expired_token(fetches, refreshes):
    client = make_client(make_token(-10))

    client.request('get', 'profile/me', level=AuthLevel.ACCESS)

    assert len(refreshes) == 1
    assert not client._profile.access_data.is_expired


def test_fresh_token_is_not_refreshed(fetches, refreshes):
    client = make_client(make_token(900))

    client.request('get', 'search', {'q': 'итд'}, level=AuthLevel.NO)
    client.request('get', 'profile/me', level=AuthLevel.ACCESS)

    assert refreshes == []
    assert len(fetches) == 2


def test_refresh_endpoint_does_not_recurse(fetches, refreshes):
    client = make_client(make_token(-10))

    client.request('post', 'v1/auth/refresh', level=AuthLevel.REFRESH)

    assert refreshes == []
    assert fetches[0]['url'] == 'v1/auth/refresh'


def test_refresh_auth_stores_new_token(refreshes):
    client = make_client(make_token(-10))
    expired = client._profile.access

    assert client.refresh_auth() == client._profile.access
    assert refreshes == [expired]
    assert client._profile.access != expired
    assert client._profile.access_valid and not client._profile.access_data.is_expired


def test_expired_token_is_not_sent_after_rejection(fetches, refreshes):
    """Обновить токен нечем - дальше ходим анонимно, а не с протухшим токеном"""
    client = make_client(make_token(-10), refresh=None)

    @api_wrapper()
    def get_something(client: Client):
        return make_response(401, {'error': 'token expired'})

    with pytest.raises(AccessTokenExpiredError):
        get_something(client)

    assert not client._profile.access_valid  # fetch подставляет токен только пока он valid


def test_api_wrapper_retries_after_token_expired(fetches, refreshes):
    """Сервер может отвергнуть токен, который по нашим часам еще жив"""
    client = make_client(make_token(900))
    responses = [make_response(401, {'error': 'token expired'}), make_response(200, {'data': {}})]

    @api_wrapper()
    def get_something(client: Client):
        return responses.pop(0)

    assert get_something(client).status_code == 200
    assert len(refreshes) == 1


@pytest.mark.parametrize(('expires_in', 'warned'), [(900, True), (-10, False)])
def test_api_wrapper_warns_if_token_rejected_but_not_expired(fetches, refreshes, caplog, expires_in, warned):
    """Если по нашим часам токен еще жив, а сервер его отверг - предупреждаем (расхождение часов / отозванная сессия)"""
    getLogger('itd').propagate = True
    client = make_client(make_token(expires_in))
    responses = [make_response(401, {'error': 'token expired'}), make_response(200, {'data': {}})]

    @api_wrapper()
    def get_something(client: Client):
        return responses.pop(0)

    with caplog.at_level(WARNING, logger='itd.request'):
        get_something(client)

    assert any('clock skew' in record.getMessage() for record in caplog.records) is warned
    assert len(refreshes) == 1


def test_api_wrapper_raises_if_retry_failed(fetches, refreshes):
    client = make_client(make_token(900))

    @api_wrapper()
    def get_something(client: Client):
        return make_response(401, {'error': 'token expired'})

    with pytest.raises(AccessTokenExpiredError):
        get_something(client)

    assert len(refreshes) == 1  # refresh and retry only once


def test_api_wrapper_does_not_retry_without_refresh_token(fetches, refreshes):
    client = make_client(make_token(900), refresh=None)

    @api_wrapper()
    def get_something(client: Client):
        return make_response(401, {'error': 'token expired'})

    with pytest.raises(AccessTokenExpiredError):
        get_something(client)

    assert refreshes == []
