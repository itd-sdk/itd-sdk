from base64 import urlsafe_b64decode
from json import loads
from _io import BufferedReader
from time import time
from typing import Any
from urllib.parse import quote
from typing import TYPE_CHECKING

from requests import Response, Session
from itd.logger import get_logger
if TYPE_CHECKING:
    from itd.client import Client

l = get_logger('request')


# ai begin ---

def _get_jhash(b: int) -> int:
    """Calculate DDoS-Guard challenge hash (JS get_jhash port)."""
    x = 123456789
    k = 0
    for i in range(1677696):
        x = ((x + b) ^ (x + (x % 3) + (x % 17) + b) ^ i) % 16776960
        if x % 117 == 0:
            k = (k + 1) % 1111
    return k


def _solve_ddos_guard(session: Session, response: Response, domain: str = 'xn--d1ah4a.com', user_agent: str = '') -> bool:
    """Solve DDoS-Guard JS challenge. Returns True if solved (duplicate request required)."""
    if '<html>' not in response.text[:500] or 'get_jhash' not in response.text:
        return False

    js_p = session.cookies.get('__js_p_')
    if not js_p:
        return False

    params = js_p.split(',')
    code = int(params[0])

    l.info('solve challenge code=%s', code)
    jhash = _get_jhash(code)
    l.info('solved jhash=%s', jhash)

    session.cookies.set('__jhash_', str(jhash), domain=domain, path='/')
    session.cookies.set('__jua_', quote(user_agent, safe=''), domain=domain, path='/')

    return True
# --- ai end

def decode_jwt_payload(jwt_token: str) -> dict[str, Any]:
    """Декодирует payload jwt.

    Args:
        jwt_token: jwt токен

    Returns:
        jwt payload
    """
    parts = jwt_token.split('.')
    if len(parts) != 3:
        raise ValueError("Not enough parts in access token")
    payload = parts[1]
    payload += '=' * ((4 - len(payload) % 4) % 4)
    decoded = urlsafe_b64decode(payload).decode('utf-8')
    return loads(decoded)


def is_token_expired(access_token: str) -> bool:
    """Истёк ли `access_token`.

    Args:
        access_token: access токен

    Returns:
        Истёк ли токен

    """
    payload = decode_jwt_payload(access_token)
    return time() - 1 >= payload['exp']


def fetch(client: 'Client', method: str, url: str, params: dict = {}, files: dict[str, tuple[str, BufferedReader | bytes]] = {}) -> Response:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        'User-Agent': client.config.user_agent,
    }
    if client.access_token:
        headers['Authorization'] = 'Bearer ' + client.access_token

    # ai begin ---
    def _do_request():
        m = method.lower()
        if m == "get":
            return client.session.get(
                f'{client.config._url_api}/{url}',
                timeout=client.config.timeout,
                params=params,
                headers=headers
            )

        return client.session.request(
            m.upper(),
            f'{client.config._url_api}/{url}',
            timeout=client.config.timeout_file if files else client.config.timeout,
            json=params,
            headers=headers,
            files=files
        )

    res = _do_request()
    if client.config.solve_challenge:
        for _ in range(3):
            if not _solve_ddos_guard(client.session, res, client.config.url, client.config.user_agent):
                break
            l.debug('ddos-guard cookies: %s', {c.name: c.value for c in client.session.cookies if c.name.startswith('__')})
            res = _do_request()
        else:
            l.warning('ddos-guard challenge not solved')
    # --- ai end

    return res


def fetch_stream(token: str, url: str, *, session: Session):
    """Fetch для SSE streaming запросов"""
    base = f'https://xn--d1ah4a.com/api/{url}'
    headers = {
        "Accept": "text/event-stream",
        "Authorization": 'Bearer ' + token,
        "Cache-Control": "no-cache",
        'Sec-WebSocket-Extensions': 'permessage-deflate',
        'Sec-WebSocket-Key': '3tMaiXFWtq34tenKN/+T4Q==',
        'Sec-WebSocket-Version': '13'
    }
    return session.get(base, headers=headers, stream=True, timeout=None)
