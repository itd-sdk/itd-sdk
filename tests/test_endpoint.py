from importlib import import_module
from inspect import signature
from pathlib import Path
from string import Formatter
from uuid import uuid4

import pytest
from helpers import make_client, make_response, make_token

import itd.api

from itd.api.auth import logout
from itd.api.comments import get_comments
from itd.api.files import upload_file
from itd.api.pins import get_pins
from itd.api.posts import get_user_posts, like_post
from itd.api.search import search
from itd.exceptions import InsufficientAuthLevelError

pytestmark = pytest.mark.usefixtures('keep_default_client')


def test_url_is_filled_from_arguments(fetches):
    client = make_client(make_token(900))
    id = uuid4()

    like_post(client, id)

    assert fetches[0]['method'] == 'post'
    assert fetches[0]['url'] == f'posts/{id}/like'
    assert fetches[0]['params'] == {}


def test_params_are_returned_by_function(fetches):
    client = make_client(make_token(900))
    post_id = uuid4()

    get_comments(client, post_id, cursor=5, limit=50)

    assert fetches[0]['url'] == f'posts/{post_id}/comments'
    assert fetches[0]['params'] == {'limit': 50, 'sort': 'popular', 'cursor': 5}


def test_default_arguments_are_used_in_url_and_params(fetches):
    client = make_client(make_token(900))

    get_user_posts(client, 'itd')

    assert fetches[0]['url'] == 'posts/user/itd'
    assert fetches[0]['params']['limit'] == 20
    assert fetches[0]['params']['sort'] == 'new'


def test_endpoint_without_body_sends_no_params(fetches):
    client = make_client(make_token(900))

    get_pins(client)

    assert fetches[0] == {'method': 'get', 'url': 'users/me/pins', 'params': {}, 'files': {}}


def test_endpoint_can_send_files(fetches):
    client = make_client(make_token(900))

    upload_file(client, 'pic.png', b'123')

    assert fetches[0]['files'] == {'file': ('pic.png', b'123')}
    assert fetches[0]['params'] == {}


def test_search_goes_through_whole_pipeline(monkeypatch, refreshes):
    """Путь целиком: эндпоинт -> Client.request -> fetch -> api_wrapper (обновление протухшего токена и повтор)"""
    client = make_client(make_token(-10))
    calls = []

    def fake_fetch(client, method, url, params={}, files={}, sse=False):
        calls.append((method, url, params))
        if len(calls) == 1:  # search с AuthLevel.NO отправляет протухший токен, сервер его отвергает
            return make_response(401, {'error': 'token expired'})
        return make_response(200, {'data': {'users': [], 'hashtags': []}})

    monkeypatch.setattr('itd.core.client.fetch', fake_fetch)

    assert search(client, 'итд', 2, 3).json()['data'] == {'users': [], 'hashtags': []}
    assert calls == [('get', 'search', {'userLimit': 2, 'hashtagLimit': 3, 'q': 'итд'})] * 2
    assert len(refreshes) == 1  # токен обновлен и запрос повторен, хотя эндпоинт с AuthLevel.NO


def test_all_url_templates_match_signatures():
    """Все имена в шаблонах url должны быть аргументами своих функций"""
    checked = 0
    for file in sorted(Path(itd.api.__file__).parent.glob('*.py')):  # все модули апи, а не список имен: он отстает от репозитория
        module = import_module(f'itd.api.{file.stem}')
        for func in vars(module).values():
            declaration = getattr(func, 'endpoint', None)
            if declaration is None:
                continue

            fields = {field for _, field, _, _ in Formatter().parse(declaration.url) if field}
            assert fields <= set(signature(func).parameters), f'{func.__name__}: {declaration.url}'
            checked += 1

    assert checked > 50


def test_endpoint_requires_declared_auth_level(fetches):
    """logout объявлен с AuthLevel.REFRESH, а у клиента только access token"""
    client = make_client(make_token(900), refresh=None)

    with pytest.raises(InsufficientAuthLevelError):
        logout(client)

    assert fetches == []
