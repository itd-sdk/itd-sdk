import base64
import json
from _io import BufferedReader
import time
from typing import Any
from urllib.parse import quote

from requests import Response, Session
from requests.exceptions import JSONDecodeError

from itd.exceptions import (
    InvalidToken, InvalidCookie, RateLimitExceeded, Unauthorized, AccountBanned, ProfileRequired
)

s = Session()

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0'


def _get_jhash(b: int) -> int:
    """Вычислить DDoS-Guard challenge hash (порт JS get_jhash)."""
    x = 123456789
    k = 0
    for i in range(1677696):
        x = ((x + b) ^ (x + (x % 3) + (x % 17) + b) ^ i) % 16776960
        if x % 117 == 0:
            k = (k + 1) % 1111
    return k


def _solve_ddos_guard(session: Session, response: Response) -> bool:
    """Решить DDoS-Guard JS challenge. Возвращает True если решён (нужен повторный запрос)."""
    if '<html>' not in response.text[:500] or 'get_jhash' not in response.text:
        return False

    js_p = session.cookies.get('__js_p_')
    if not js_p:
        return False

    params = js_p.split(',')
    code = int(params[0])

    print('solving DDoS-Guard challenge (code=%s)', code)
    jhash = _get_jhash(code)
    print('solved: jhash=%s', jhash)

    session.cookies.set('__jhash_', str(jhash), domain='xn--d1ah4a.com', path='/')
    session.cookies.set('__jua_', quote(UA, safe=''), domain='xn--d1ah4a.com', path='/')

    return True


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

    def _do_request():
        m = method.lower()
        if m == "get":
            return s.get(base, timeout=120 if files else 20, params=params, headers=headers)
        return s.request(m.upper(), base, timeout=120 if files else 20, json=params, headers=headers, files=files)

    res = _do_request()
    for _ in range(3):
        if not _solve_ddos_guard(s, res):
            break
        res = _do_request()
    else:
        print('DDoS-Guard challenge not solved after 3 attempts')

    if res.status_code == 204:
        return res

    if not res.ok:
        print(res.text)

    try:
        if res.json().get('error') == 'Too Many Requests':
            raise RateLimitExceeded(res.json().get('retry_after', 0))
        if res.json().get('error', {}) == 'token expired' or res.json().get('error', {}).get('code') == 'UNAUTHORIZED':
            raise Unauthorized()
        if res.json().get('error', {}).get('code') == 'RATE_LIMIT_EXCEEDED':
            raise RateLimitExceeded(res.json()['error'].get('retryAfter', 0))
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
        "Origin": "https://xn--d1ah4a.com",
        'User-Agent': UA,
        "Cookie": cookies
    }
    if token:
        headers['Authorization'] = 'Bearer ' + token

    def _do_request():
        if method == 'get':
            return s.get(f'https://xn--d1ah4a.com/api/{url}', timeout=20, params=params, headers=headers)
        return s.request(method, f'https://xn--d1ah4a.com/api/{url}', timeout=20, json=params, headers=headers)

    res = _do_request()
    for _ in range(3):
        if not _solve_ddos_guard(s, res):
            break
        res = _do_request()
    else:
        print('DDoS-Guard challenge not solved after 3 attempts')

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
