from __future__ import annotations

from atexit import register
from datetime import datetime
from functools import cached_property
from io import BufferedReader
from threading import RLock
from typing import TYPE_CHECKING
from uuid import UUID

from requests import Response, Session
from requests.adapters import HTTPAdapter

from itd.api.auth import change_password, logout, refresh_token, sign_in
from itd.core.auth import AuthMethod, apply_auth, env_auth, interactive_auth
from itd.core.captcha import get_turnstile
from itd.core.config import Config
from itd.core.default import maybe_get_default_client, set_default_client
from itd.core.dwell import DwellTracker
from itd.core.logger import get_logger
from itd.core.profile import Profile, clear_anon_profile
from itd.core.request import fetch
from itd.core.visibility import VisibilityTracker
from itd.enums import AuthLevel
from itd.exceptions import AccessTokenExpiredError, InsufficientAuthLevelError, SessionExpiredError

if TYPE_CHECKING:
    from itd.models.post import Post
    from itd.models.user import Me

l = get_logger('client')


class Client:
    def __init__(self, name: str, config: Config | None = None, auth: AuthMethod | None = None):
        l.info('init client %s', name)
        self.config = config or Config()

        self.auth_level: AuthLevel = AuthLevel.NO
        self._profile: Profile = Profile.get(name)

        self._refresh_lock = RLock()  # so background timers and main thread dont refresh token simultaneously # еба он мой стиль коментов спиздил

        self.session = Session()
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=10, pool_block=False)  # idk what is this, (claude added) just for better stability
        self.session.mount('https://', adapter)

        if maybe_get_default_client() is None or self.config.is_default:
            set_default_client(self)

        if name != 'no-auth':
            self._credtest = True
            if auth is not None:
                apply_auth(self, auth)
            elif not env_auth(self):
                interactive_auth(self)
        self._credtest = False

        self._set_from_profile()
        self._profile.flush()

        self.dwell_tracker = DwellTracker(self)
        self.dwell_tracker.start()

        self.visibility = VisibilityTracker(self)
        self.visibility.start()

    def _set_from_profile(self):
        if self._profile.access and self._profile.access_valid:
            self.auth_level = AuthLevel.ACCESS

        if self._profile.refresh and self._profile.refresh_valid:
            self.session.cookies.set(self.config.refresh_token_cookie_name, self._profile.refresh, path='/')
            self.auth_level = AuthLevel.REFRESH

        if self._profile.email and self._profile.password and self._profile.creds_valid:
            self.auth_level = AuthLevel.LOGIN

    def login(self, turnstile: str | None = None) -> str:
        """Обновить refresh token

        Returns:
            str: Токен
        """
        with self._refresh_lock:
            res = sign_in(
                self, self._profile.email, self._profile.password, 'turnstileToken', turnstile or get_turnstile(self)
            )  # 'turnstileToken' пока загулшка, ждем когда вернут капчу от итд
            self._profile.set_access(res.json().get('accessToken') or res.json()['token'])
            self._profile.set_refresh(res.cookies[self.config.refresh_token_cookie_name], set_expire=True)
            self._profile.flush()
            self._set_from_profile()

            assert self._profile.refresh
            return self._profile.refresh

    def refresh_auth(self) -> str:
        """Обновить access token

        Returns:
            str: Токен
        """

        with self._refresh_lock:
            l.debug('refresh access_token')

            res = refresh_token(self)
            self._profile.set_access(res.json().get('accessToken') or res.json()['token'])
            if self.config.refresh_token_cookie_name in res.cookies:
                self._profile.set_refresh(res.cookies[self.config.refresh_token_cookie_name])
            self._profile.flush()
            self._set_from_profile()

            assert self._profile.access
            return self._profile.access

    @property
    def visible_posts(self) -> list[Post]:
        """Посты, видимые прямо сейчас"""
        return self.visibility.posts

    @property
    def last_active(self) -> datetime:
        return self.visibility.last_active

    def set_active(self):  # call when user is active (scroll, move etc)
        """Отметить активность пользователя"""
        self.visibility.set_active()

    def update_post_stats(self):
        """Обновить статистику видимых постов"""
        self.visibility.update_stats()

    def _before_request(self, url: str, level: AuthLevel = AuthLevel.ACCESS):
        if level == AuthLevel.NO or self._credtest:
            return

        if level >= AuthLevel.REFRESH and ((self._profile.refresh and self._profile.is_refresh_expired) or not self._profile.refresh_valid):
            self._profile.refresh_valid = False
            if self.auth_level == AuthLevel.LOGIN:
                self.login()
            else:
                l.error('not enough level to re-login')
                if not self.config.bypass_auth_level:
                    raise SessionExpiredError()

        if (
            url != 'v1/auth/refresh'
            and level >= AuthLevel.ACCESS
            and ((self._profile.access_data and self._profile.access_data.is_expired) or not self._profile.access_valid)
        ):
            self._profile.access_valid = False
            if self.auth_level >= AuthLevel.REFRESH:
                self.refresh_auth()
            else:
                l.error('not enough level to refresh access_token')
                if not self.config.bypass_auth_level:
                    raise AccessTokenExpiredError()

    def request(
        self,
        method: str,
        url: str,
        params: dict = {},
        files: dict[str, tuple[str, BufferedReader | bytes]] = {},
        sse: bool = False,
        level: AuthLevel = AuthLevel.ACCESS
    ) -> Response:
        l.debug('%s %s params=%s authlevel=%s', ('SSE ' if sse else '') + method.upper(), url, params, level.value)

        if level > self.auth_level and not self.config.bypass_auth_level and not self._credtest:
            raise InsufficientAuthLevelError(self.auth_level, level)

        self._before_request(url, level=level)
        return fetch(self, method, url, params, files, sse=sse)

    @property
    def user_id(self) -> UUID:
        assert self._profile.access_data
        return self._profile.access_data.subject_id

    @cached_property
    def user(self) -> Me:
        from itd.models.user import Me

        return Me(client=self)

    def _process_exc_callbacks(self, exception: Exception):
        # l.debug([v for k, v in self.config.on_exceptions.items() if k in exception.__class__.mro()])
        for callback in [v for k, v in self.config.on_exceptions.items() if k in exception.__class__.mro()]:
            callback(exception)

    def logout(self):
        """Выход из аккаунта"""
        res = logout(self)
        res.raise_for_status()

    def change_password(self, old: str, new: str) -> None:
        """Смена пароля

        Args:
            old (str): Старый пароль
            new (str): Новый пароль

        Raises:
            NoCookie: Нет cookie
            SamePasswordError: Одинаковые пароли
            InvalidOldPasswordError: Старый пароль неверный

        """
        # if not self.refresh_token:
        # raise InsufficientAuthLevelError()

        change_password(self, old, new)


def init_client(name: str | None = None, config: Config | None = None, auth: AuthMethod | None = None) -> Client:
    if name == 'anon':
        clear_anon_profile()
        register(clear_anon_profile)
    return Client(name or 'default', config=config, auth=auth)


def init_not_authed_client(config: Config | None = None):
    return Client('no-auth', config=config)
