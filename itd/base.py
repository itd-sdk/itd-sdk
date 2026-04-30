from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
from functools import wraps
from time import sleep
from datetime import datetime, timedelta

from requests import Response
from requests.exceptions import JSONDecodeError
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefinedType

from itd._default import get_default_client
from itd.logger import get_logger
from itd.exceptions import ITDException, ValidationError, RateLimitError, InvalidAccessTokenError, DEFAULT_ERRORS
from itd.enums import All, ALL, DebugResponseMode, RateLimitMode
if TYPE_CHECKING:
    from itd.client import Client


l = get_logger('base')

def _getattr(self: object, name: str, default: Any | None = None) -> Any:
    try:
        return object.__getattribute__(self, name)
    except AttributeError:
        return default


def _field_has_default(cls: type, name: str) -> bool:
    """Returns True if the field is declared as Field(...) with a default value."""
    for klass in cls.__mro__:
        val = klass.__dict__.get(name)
        if isinstance(val, FieldInfo):
            return not isinstance(val.default, PydanticUndefinedType) or val.default_factory is not None
    return False


class ITDBaseModel:
    _refreshable: bool = True
    _loaded: bool = False
    _loading: bool = False
    _load_with_parent: bool = True # load parent model if model called
    _validator: Callable[[Any], type[BaseModel]] | None = None # callable (pls use lambda), becuase we havent validator at that moment (it depends on this class)

    def __init__(self, client: Client | None = None) -> None:
        self._client = client or get_default_client()
        self._fields_from_data: set[str] = set()

    def __setattr__(self, name: str, value: Any) -> None:
        if isinstance(value, ITDBaseModel) and (client := _getattr(self, '_client')): # ai
            value._client = client
        object.__setattr__(self, name, value)

    @property
    def client(self) -> Client:
        return self._client

    def _token(self, client: Client | None = None) -> str: # should be property, but it needs client param
        return (client or self._client).token

    def refresh(self) -> Any:
        l.warning('refresh is not implemented but have called')
        self._loaded = True


    def __getattribute__(self, name: str) -> Any:
        if _getattr(self, '_refreshable') and not name.startswith('_') or name in ('client', 'model_fields_set'):
            try:
                attr = _getattr(self, name)
            except AttributeError:
                attr = None

            if callable(attr):
                return object.__getattribute__(self, name)

            fields_from_data = _getattr(self, '_fields_from_data', ())
            triggers = {
                'default': name not in fields_from_data and _field_has_default(type(self), name),
                'none': attr is None and not _field_has_default(type(self), name),
                'field-info': isinstance(attr, FieldInfo)
            }
            if (
                not _getattr(self, '_loaded') and
                any(triggers.values()) and
                _getattr(self, 'client').config.auto_load and
                not (name == 'comments' and not _getattr(self, 'client').config.load_comments_from_post) # да я хотел сделать нормально, поставить проперти на comments и тд, но это херня кака ято крч просто нахардкожу
            ):
                l.info('load %s.%s reason=%s', self.__class__.__name__.lower(), name,
                    next((k for k, v in triggers.items() if v))
                )
                self.refresh()

        return object.__getattribute__(self, name)



class ITDList(ITDBaseModel, list):
    _limit: int = 20
    _get_total = None
    _refreshable = False
    has_more = True
    idx = 0

    def _fetch(self, client: Client, limit: int) -> dict:
        return {}

    # edited by calude, thats so fucking crazy pagination
    # ai begin ---
    def load(self, count: int | All | None = None, limit: int | None = None, client: Client | None = None):
        if not (self.has_more or self.client.config.force_load_lists):
            return self

        limit = limit or self._limit
        if isinstance(count, int) and count < limit:
            limit = count

        # None = load one batch (limit), All = load everything, int = load exactly N
        left = None if isinstance(count, All) else (count or limit)

        while left is None or left > 0:
            batch = limit if left is None else min(limit, left)
            data = self._fetch(client or self.client, batch)
            objects = self._get_objects(data)
            self.has_more = self._get_has_more(data)
            if self._get_cursor(data) is not None:
                self.cursor = self._get_cursor(data)

            if self._get_total:
                self.total = self._get_total(data)
                if getattr(self, '_min_total', None) and self._min_total > self.total:
                    raise IndexError(f'Given index ({self._min_total - 1}) is too high. Total items is {self.total}')

            if left is not None:
                left -= len(objects)

            l.info('fetched %s %s (was %s) cursor=%s has_more=%s', len(objects), self.__class__.__name__.lower(), len(self), self.cursor, self.has_more)
            self._extend(objects, client or self.client)

            if not self.has_more or not objects:
                break

        return self
    # --- ai end

    def _extend(self, objects: list, client: Client):
        pass

    @staticmethod
    def _get_has_more(data: dict) -> bool:
        return True

    @staticmethod
    def _get_cursor(data: dict):
        return 0

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return []

    def refresh(self, count: int | All | None = None, client: Client | None = None, limit: int | None = None):
        count = count or len(self)
        self.clear()
        self.cursor = None
        return self.load(count, limit, client)

    def load_all(self, limit: int | None = None, client: Client | None = None):
        return self.load(ALL, limit, client)

    def __getitem__(self, index: int):  # pyright: ignore[reportIncompatibleMethodOverride]
        if index > len(self) - 1 and self.client.config.load_on_getitem:
            self._min_total = index + 1
            if isinstance(self.client.config.load_on_getitem_count, All):
                l.debug('getitem load all')
                self.load_all()
            else:
                l.debug('getitem load %s', index - len(self) + self.client.config.load_on_getitem_count)
                self.load(index - len(self) + self.client.config.load_on_getitem_count)
        return super().__getitem__(index)

    def __next__(self):
        if getattr(self, 'total', None) and self.idx >= self.total:
            raise StopIteration()
        if self.idx >= len(self) and (self.has_more or self.client.config.force_load_lists):
            l.debug('not enough items to call next - load')
            self.load()
        if self.idx >= len(self):
            raise StopIteration()
        item = self[self.idx]
        self.idx += 1
        return item

    def __iter__(self):
        self.idx = 0
        return self

    @property
    def all(self):
        return self.load_all()


def refresh_wrapper(func):
    @wraps(func)
    def wrapper(self, client: Client | None = None):
        # if self._loading:
        #     return

        # self._loading = True
        data = func(self, client or self.client)
        if self._validator:
            validated = self._validator().model_validate(data)
            self._fields_from_data = validated.model_fields_set
            l.debug('refresh %s', self.__class__.__name__.lower())
            for name, value in validated.__dict__.items():
                setattr(self, name, value)

        # self._loading = False
        self._loaded = True

    return wrapper


def _filter_bytes(args: tuple):
    filtered = []
    for arg in args:
        if isinstance(arg, bytes):
            filtered.append('_bytecode_')
        else:
            filtered.append(arg)
    return filtered

def catch_errors(*exceptions: ITDException):
    def decorator(func):
        @wraps(func)
        def wrapper(client: Client, *args, **kwargs) -> Response | None:
            l.info('exec %s %s %s', func.__name__, _filter_bytes(args), kwargs)
            res: Response = func(client, *args, **kwargs)

            assert isinstance(res, Response)
            if res.status_code == 204:
                return res

            if client.config.debug_response == DebugResponseMode.BEFORE:
                l.debug('response (raw): %s', res.text)

            try:
                json = res.json()
            except JSONDecodeError:
                json = {}
                l.warning('failed to parse json: %s', res.text[:1000])

            for exception in DEFAULT_ERRORS + exceptions:
                if (
                    getattr(exception, '_reply_comment_user_not_found', False) and res.status_code == 500 and 'Failed query' in res.text or
                    getattr(exception, '_delete_comment_not_found', False) and res.status_code == 500 and res.text == 'Комментарий не найден' or
                    getattr(exception, '_liked_posts_user_not_found', False) and res.status_code == 404 and res.text == 'NOT_FOUND' or
                    isinstance(exception, InvalidAccessTokenError) and res.text == 'UNAUTHORIZED' or
                    getattr(exception, '_report_target_not_found', False) and res.status_code == 400 and 'не найден' in json.get('error', {}).get('message', '') or
                    getattr(exception, '_subscription_not_found', False) and json.get('error') == 'Активная подписка не найдена' or
                    getattr(exception, '_hashtag_not_found', False) and json.get('data', {}).get('hashtag', '') is None or
                    getattr(exception, '_notification_read_error', False) and json.get('success') is False or
                    isinstance(exception, ValidationError) and res.status_code == 422 and 'found' in json or
                    isinstance(exception, RateLimitError) and json.get('error') == 'Too Many Requests' or

                    exception.status_code is not None and res.status_code == exception.status_code or
                    exception.code is not None and json.get('error', {}).get('code') == exception.code or
                    exception.message is not None and json.get('error', {}).get('message') == exception.message
                ):
                    if isinstance(exception, ValidationError) and json.get('error', {}).get('code') == exception.code:
                        exception.text = json['error']['message']
                    if isinstance(exception, RateLimitError) and isinstance(json.get('error'), dict) and json['error'].get('code') == exception.code:
                        exception.retry_after = json['error'].get('retryAfter', 0)

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

        return wrapper
    return decorator


def rate_limit(delay_min: float | None = None, delay_mid: float | None = None, delay_max: float | None = None):
    def decorator(func):
        @wraps(func)
        def wrapper(client: Client, *args, **kwargs) -> Response | None:
            if func.__name__ in client.config.rate_limit_actions:
                delay = client.config.rate_limit_actions[func.__name__]
            elif client.config.rate_limit == RateLimitMode.NO:
                delay = 0
            elif any((delay_min, delay_mid, delay_max)):
                delay = eval(f'delay_{client.config.rate_limit.value}') or next((i for i in (delay_min, delay_mid, delay_max) if i is not None))
            else:
                delay = client.config._rate_limit_default

            if datetime.now() - timedelta(seconds=delay) < client.last_actions.get(func.__name__, datetime(2013, 2, 16)):  # my birthday actually
                delay -= (datetime.now() - client.last_actions[func.__name__]).seconds
                l.debug('anti rate limit on %s; wait %ss', func.__name__, delay)
                sleep(delay)
            client.last_actions[func.__name__] = datetime.now()

            while True:
                try:
                    return func(client, *args, **kwargs)
                except RateLimitError as e:
                    l.info('rate limit on %s; wait %ss', func.__name__, e.retry_after or 10)
                    sleep(e.retry_after or 10)

        return wrapper
    return decorator
