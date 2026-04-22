from uuid import UUID
from _io import BufferedReader
from datetime import datetime
from dataclasses import dataclass, field

from requests import Session
from requests.adapters import HTTPAdapter

from itd._default import _default_client, set_default_client
from itd.exceptions import NoCookie, Unauthorized
from itd.hashtag import Hashtag
from itd.request import fetch, decode_jwt_payload
from itd.enums import RateLimitMode, All, DebugResponseMode
from itd.user import Me, User
from itd.routes.auth import refresh_token, change_password, logout
from itd.routes.search import search
from itd.logger import get_logger


l = get_logger('client')


@dataclass
class Config:
    rate_limit: RateLimitMode = RateLimitMode.MID
    rate_limit_default: int | None = None # overrides ratelimit mode  # rate limit for standard actions
    rate_limit_actions: dict[str, float | int] = field(default_factory=lambda: {}) # overrides ratelimit mode  # custom rate limits for specific actions (eg. {'add_comment': 10})
    # is_logging_enabled: bool = True # TODO
    # logging_level = 'DEBUG'
    is_default: bool = False
    userposts_add_pinned_post: bool = True
    auto_load: bool = True
    load_on_getitem: bool = True
    load_on_getitem_count: int | All = 1
    force_load_lists: bool = False # load lists even if has_more is False
    debug_response: DebugResponseMode = DebugResponseMode.NO
    # parse_mode = None

    def __post_init__(self):
        if self.rate_limit_default:
            self._rate_limit_default = self.rate_limit_default
        elif self.rate_limit == RateLimitMode.MIN:
            self._rate_limit_default = 0
        elif self.rate_limit == RateLimitMode.MID:
            self._rate_limit_default = 0.2
        else:
            self._rate_limit_default = 0.4




class Client:
    access_token: str | None = None
    refresh_token: str | None = None
    last_actions: dict[str, datetime] = {}
    default_delay: float = 0.2
    _user = None

    def __init__(self, refresh_token: str | None = None, access_token: str | None = None, config: Config = Config()):
        l.info('init client refresh=%s access=%s', refresh_token is not None, access_token is not None)
        self.config = config

        self.session = Session()
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=10, pool_block=False) # idk what is this, (claude added) just for better stability
        self.session.mount('https://', adapter)

        if access_token:
            self.access_token = access_token.replace('Bearer ', '')

        if refresh_token:
            self.refresh_token = refresh_token
            self.session.cookies.set('refresh_token', refresh_token, path='/', domain='xn--d1ah4a.com')
            if access_token is None:
                self.refresh_auth()

        if _default_client is None or config.is_default:
            set_default_client(self)

    def request(self, method: str, url: str, params: dict = {}, files: dict[str, tuple[str, BufferedReader | bytes]] = {}):
        """Сделать запрос

        Args:
            method (str): Метод
            url (str): URL
            params (dict, optional): Параметры. Defaults to {}.
            files (dict[str, tuple[str, BufferedReader | bytes]], optional): Файлы. Defaults to {}.
        """
        l.debug('%s %s params=%s', method.upper(), url, params)
        def _fetch():
            return fetch(self.token, method, url, params, files, session=self.session)

        if not self.refresh_token:
            return _fetch()

        try:
            return _fetch()
        except Unauthorized:
            self.refresh_auth()
            return _fetch()

    def refresh_auth(self) -> str:
        """Обновить access token

        Raises:
            NoCookie: Нет cookie

        Returns:
            str: Токен
        """
        l.debug('refresh token')
        if not self.refresh_token:
            raise NoCookie()

        res = refresh_token(self.session)
        res.raise_for_status()

        self.access_token = res.json()['accessToken']

        assert self.access_token
        return self.access_token


    @property
    def token(self) -> str:
        assert self.access_token, 'Access token not refreshed yet'
        return self.access_token

    @property
    def user_id(self) -> UUID:
        return UUID(decode_jwt_payload(self.token)['sub'])

    @property
    def user(self):
        if not self._user:
            self._user = Me(self)
        return self._user


    def logout(self) -> dict:
        """Выход из аккаунта

        Raises:
            NoCookie: Нет cookie

        Returns:
            dict: Ответ API
        """
        # if not self.cookies:
            # raise NoCookie()

        res = logout(self)
        res.raise_for_status()

        return res.json()


    def change_password(self, old: str, new: str) -> None:
        """Смена пароля

        Args:
            old (str): Старый пароль
            new (str): Новый пароль

        Raises:
            NoCookie: Нет cookie
            SamePassword: Одинаковые пароли
            InvalidOldPassword: Старый пароль неверный

        """
        if not self.refresh_token:
            raise NoCookie()

        change_password(self, old, new)


    def search(self, query: str, hashtags_limit: int = 20, users_limit: int = 20) -> tuple[list[User], list[Hashtag]]:
        res = search(self, query, users_limit, hashtags_limit).json()['data']
        return [User._from_dict(user, False, self) for user in res['users']], [Hashtag._from_dict(hashtag, self) for hashtag in res['hashtags']]
