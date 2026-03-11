import base64
import json
from _io import BufferedReader
import time
from typing import Any

from requests import Response, Session
from requests.exceptions import JSONDecodeError

from itd.exceptions import (
    InvalidToken, InvalidCookie, RateLimitExceeded, Unauthorized, AccountBanned, ProfileRequired
)

s = Session()


def decode_jwt_payload(jwt_token: str) -> dict[str, Any]:
    """Декодирует pyload jwt.

    Args:
        jwt_token: jwt токен

    Returns:
        jwt payload
    """
    parts = jwt_token.split('.')
    if len(parts) != 3:
        raise ValueError("access токен состоит из трёх сегментов")
    payload = parts[1]
    payload += '=' * ((4 - len(payload) % 4) % 4)
    decoded = base64.urlsafe_b64decode(payload).decode('utf-8')
    return json.loads(decoded)


def is_token_expired(access_token: str) -> bool:
    """Истёк ли `access_token`.

    Args:
        access_token: access токен

    Returns:
         Истёк ли токен

    """
    payload = decode_jwt_payload(access_token)
    return time.time() - 1 >= payload['exp']


def fetch(token: str, method: str, url: str, params: dict = {},
          files: dict[str, tuple[str, BufferedReader | bytes]] = {}) -> Response:
    base = f'https://xn--d1ah4a.com/api/{url}'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Authorization": 'Bearer ' + token
    }
    method = method.lower()
    if method == "get":
        res = s.get(base, timeout=120 if files else 20, params=params, headers=headers)
    else:
        res = s.request(method.upper(), base, timeout=120 if files else 20, json=params, headers=headers, files=files)

    if res.status_code == 204:
        return res

    if not res.ok:
        print(res.text)

    try:
        if res.json().get('error') == 'Too Many Requests':
            raise RateLimitExceeded(res.json().get('retry_after', 0))
        if res.json().get('error', {}).get('code') == 'RATE_LIMIT_EXCEEDED':
            raise RateLimitExceeded(res.json()['error'].get('retryAfter', 0))
        if res.json().get('error', {}).get('code') == 'UNAUTHORIZED':
            raise Unauthorized()
        if res.json().get('error', {}).get('code') == 'ACCOUNT_BANNED':
            raise AccountBanned()
        if res.json().get('error', {}).get('code') == 'PROFILE_REQUIRED':
            raise ProfileRequired()
    except (JSONDecodeError, AttributeError):
        print('fail to parse json')

    return res


def fetch_stream(token: str, url: str):
    """Fetch для SSE streaming запросов"""
    base = f'https://xn--d1ah4a.com/api/{url}'
    headers = {
        "Accept": "text/event-stream",
        "Authorization": 'Bearer ' + token,
        "Cache-Control": "no-cache"
    }
    return s.get(base, headers=headers, stream=True, timeout=None)


def set_cookies(cookies: str):
    for cookie in cookies.split('; '):
        s.cookies.set(cookie.split('=')[0], cookie.split('=')[-1], path='/', domain='xn--d1ah4a.com')


def auth_fetch(cookies: str, method: str, url: str, params: dict = {}, token: str | None = None) -> Response:
    headers = {
        "Host": "xn--d1ah4a.com",
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Referer": "https://xn--d1ah4a.com/",
        "Content-Type": "application/json",
        "Origin": "https://xn--d1ah4a.com",
        "Connection": "keep-alive",
        "Cookie": cookies
    }
    if token:
        headers['Authorization'] = 'Bearer ' + token

    if method == 'get':
        res = s.get(f'https://xn--d1ah4a.com/api/{url}', timeout=20, params=params, headers=headers)
    else:
        res = s.request(method, f'https://xn--d1ah4a.com/api/{url}', timeout=20, json=params, headers=headers)

    if res.text == 'UNAUTHORIZED':
        raise InvalidToken()
    try:
        if res.json().get('error') == 'Too Many Requests':
            raise RateLimitExceeded(0)
        if res.json().get('error', {}).get('code') == 'RATE_LIMIT_EXCEEDED':
            raise RateLimitExceeded(res.json()['error'].get('retryAfter', 0))
        if res.json().get('error', {}).get('code') in ('SESSION_NOT_FOUND', 'REFRESH_TOKEN_MISSING', 'SESSION_REVOKED',
                                                       'SESSION_EXPIRED'):
            raise InvalidCookie(res.json()['error']['code'])
        if res.json().get('error', {}).get('code') == 'UNAUTHORIZED':
            raise Unauthorized()
    except JSONDecodeError:
        print('fail to parse json')

    return res
