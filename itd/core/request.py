from base64 import urlsafe_b64decode
from dataclasses import dataclass, field
from functools import wraps
from inspect import signature
from io import BufferedReader
from json import loads
from time import sleep
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import quote

from requests import Response, Session
from requests.exceptions import JSONDecodeError

from itd.core.default import get_config, limiters, limits
from itd.core.logger import get_logger
from itd.enums import AuthLevel, DebugResponseMode
from itd.exceptions import (
    DEFAULT_ERRORS,
    AccessTokenExpiredError,
    InvalidAccessTokenError,
    ITDException,
    SessionExpiredError,
    SessionNotFoundError,
    SessionRevokedError
)

if TYPE_CHECKING:
    from itd.core.client import Client

l = get_logger('request')  # noqa: E741


def _get_jhash(b: int) -> int:  # ai
    """Calculate DDoS-Guard challenge hash (JS get_jhash port)."""
    x = 123456789
    k = 0
    for i in range(1677696):
        x = ((x + b) ^ (x + (x % 3) + (x % 17) + b) ^ i) % 16776960
        if x % 117 == 0:
            k = (k + 1) % 1111
    return k


def _solve_ddos_guard(session: Session, response: Response, user_agent: str = '') -> bool:  # ai
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

    session.cookies.set('__jhash_', str(jhash), path='/')
    session.cookies.set('__jua_', quote(user_agent, safe=''), path='/')

    return True


def decode_jwt_payload(jwt_token: str) -> dict[str, Any]:
    """Декодирует payload jwt.

    Args:
        jwt_token: jwt токен

    Returns:
        jwt payload
    """
    parts = jwt_token.split('.')
    if len(parts) != 3:
        raise ValueError('Not enough parts in access token')
    payload = parts[1]
    payload += '=' * ((4 - len(payload) % 4) % 4)
    decoded = urlsafe_b64decode(payload).decode('utf-8')
    return loads(decoded)


def fetch(client: 'Client', method: str, url: str, params: dict = {}, files: dict[str, tuple[str, BufferedReader | bytes]] = {}, sse: bool = False) -> Response:
    headers = {'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'}
    if client.config._user_agent:
        headers['User-Agent'] = client.config._user_agent
    if client._profile.access and client._profile.access_valid:
        headers['Authorization'] = 'Bearer ' + client._profile.access
    if sse:
        headers['Accept'] = 'text/event-stream'
        headers.update(
            {
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Referer': 'https://xn--d1ah4a.com/',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-origin'
            }
        )
    else:
        headers['Accept'] = 'application/json'

    def _do_request():
        m = method.lower()
        if m == 'get':
            return client.session.get(f'{client.config.url}/{url}', timeout=None if sse else client.config._timeout, params=params, headers=headers, stream=sse)

        return client.session.request(
            m.upper(),
            f'{client.config.url}/{url}',
            timeout=None if sse else client.config.timeout_file if files else client.config._timeout,
            json=params,
            headers=headers,
            stream=sse,
            files=files
        )

    res = _do_request()
    if client.config.solve_challenge and not sse:
        for _ in range(3):
            if not _solve_ddos_guard(client.session, res, client.config._user_agent):
                break
            l.debug('ddos-guard cookies: %s', {c.name: c.value for c in client.session.cookies if c.name.startswith('__')})
            res = _do_request()
        else:
            l.warning('ddos-guard challenge not solved')

    return res


def fetch_sse(client: 'Client', url: str, params: dict = {}):
    """Fetch для SSE streaming запросов"""
    base = f'https://xn--d1ah4a.com/api/{url}'
    headers = {
        'Accept': 'text/event-stream',
        'Authorization': f'Bearer {client._profile.access}',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://xn--d1ah4a.com/',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-origin',
        'TE': 'trailers',
        'User-Agent': client.config._user_agent
    }
    return client.session.get(base, headers=headers, params=params, stream=True, timeout=None)


@dataclass
class Payload:
    """Тело запроса эндпоинта: параметры и файлы"""

    params: dict = field(default_factory=dict)
    files: dict[str, tuple[str, BufferedReader | bytes]] = field(default_factory=dict)


def _filter_bytes(args: tuple):
    filtered = []
    for arg in args:
        if isinstance(arg, bytes):
            filtered.append('_bytecode_')
        else:
            filtered.append(arg)
    return filtered


def _find_error(res: Response, json: dict, exceptions: tuple[ITDException, ...]) -> ITDException | None:
    """Найти ошибку, под которую подходит ответ

    Args:
        res (Response): Ответ
        json (dict): Тело ответа
        exceptions (tuple[ITDException, ...]): Ошибки эндпоинта (проверяются после общих)

    Returns:
        ITDException | None: Ошибка (None если ответ успешный)
    """
    for declaration in DEFAULT_ERRORS + exceptions:
        if declaration.matches(res, json):
            return declaration.prepare(json)
    return None


def api_wrapper(*exceptions: ITDException):
    def decorator(func):
        @wraps(func)
        def wrapper(client: 'Client', *args, **kwargs) -> Response | None:
            name = func.__name__
            access_reauthed = False
            refresh_reauthed = False

            def exec():
                nonlocal access_reauthed, refresh_reauthed
                l.info('exec %s %s %s', name, _filter_bytes(args), kwargs)

                config = get_config()
                is_first = True
                if name in limits and limits[name] in limiters:
                    limiter = limiters[limits[name]]
                    if config.auto_acquire:
                        limiter.acquire()
                    is_first = not limiter.used
                    limiter.request()

                ip_limiter = config.ip_limiter
                if ip_limiter:
                    ip_limiter.acquire()

                res: Response = func(client, *args, **kwargs)

                assert isinstance(res, Response)
                if res.status_code == 204:
                    if client.config.debug_response != DebugResponseMode.NO:
                        l.debug('no response')
                    return res

                remaining = int(res.headers.get('x-ratelimit-remaining', 0))
                limit = int(res.headers.get('x-ratelimit-limit', 0))
                limits[name] = limit

                if limit not in limiters and config.limiter is not None:
                    limiters[limit] = config.limiter(limit)

                if limit in limiters and (config.auto_acquire or is_first):
                    limiters[limit].sync(remaining)

                if client.config.debug_response == DebugResponseMode.BEFORE:
                    l.debug('response (raw): %s', res.text)

                try:
                    json = res.json()
                except JSONDecodeError:
                    json = {}
                    l.warning('failed to parse json: %s', res.text[:1000])

                exception = _find_error(res, json, exceptions)
                if exception is not None:
                    # token is checked before the request, but server still can reject it (clock skew, revoked session) - refresh and repeat the request once, before callbacks
                    if isinstance(exception, (AccessTokenExpiredError, InvalidAccessTokenError)) and not access_reauthed and not client._credtest:
                        client._profile.access_valid = False
                        client._profile.flush()
                        if name != 'refresh_token':
                            access_reauthed = True
                            l.warning('%s on %s: refresh access_token and retry', exception.__class__.__name__, name)
                            client.refresh_auth()
                            return exec()

                    if (
                        isinstance(exception, (SessionExpiredError, SessionNotFoundError, SessionRevokedError))
                        and not refresh_reauthed
                        and not client._credtest
                    ):
                        client._profile.refresh_valid = False
                        client._profile.flush()
                        if name != 'sign_in':
                            refresh_reauthed = True
                            l.warning('%s on %s: refresh refresh_token and retry', exception.__class__.__name__, name)
                            client.login()
                            return exec()

                    client._process_exc_callbacks(exception)
                    raise exception

                if client.config.debug_response == DebugResponseMode.AFTER:
                    l.debug('response: %s', json)
                if client.config.debug_response == DebugResponseMode.KEYS:
                    if 'data' in json:
                        l.debug('response keys: data - %s', list(json['data'].keys()))
                    else:
                        l.debug('response keys: %s', list(json.keys()))
                res.raise_for_status()
                return res

            if not client.config._retry_enabled:
                return exec()

            def _try():
                try:
                    return exec()
                except client.config._retry_exceptions as e:
                    if getattr(e, 'retry_after', 0) > client.config.retry_max_retry_after:
                        l.error('too large rate limit')
                        raise

                    retry_after = getattr(e, 'retry_after', 0) or client.config.retry_delay
                    l.warning('%s on %s: wait %ss', e.__class__.__name__, name, retry_after)
                    sleep(retry_after)
                    if name in limits and limits[name] in limiters:
                        limiters[limits[name]].on_limit()

            if client.config.retry_max_retries:
                for _ in range(client.config.retry_max_retries):
                    if (res := _try()) is not None:
                        return res
            else:
                while True:
                    if (res := _try()) is not None:
                        return res
            raise RuntimeError('All retries exceeded')

        return wrapper

    return decorator


def endpoint(method: str, url: str, *exceptions: ITDException, sse: bool = False, level: AuthLevel = AuthLevel.ACCESS):
    def decorator(func: Callable[..., dict | Payload | None]):
        params = signature(func) if '{' in url else None  # аргументы нужно связывать, только если url шаблонный

        @wraps(func)
        def request(client: 'Client', *args, **kwargs) -> Response:
            payload = func(client, *args, **kwargs) or Payload()
            if isinstance(payload, dict):
                payload = Payload(payload)

            if params is None:
                path = url
            else:
                bound = params.bind(client, *args, **kwargs)
                bound.apply_defaults()
                path = url.format(**bound.arguments)

            return client.request(method, path, payload.params, payload.files, sse=sse, level=level)

        return request if sse else api_wrapper(*exceptions)(request)

    return decorator
