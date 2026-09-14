from dataclasses import dataclass, field
from typing import Callable, Literal

from requests.exceptions import RequestException
from requests.utils import default_user_agent

from itd.core.utils import get_sdk_user_agent
from itd.enums import BATCH, All, Batch, DebugResponseMode, ParseMode, UserAgent
from itd.exceptions import RateLimitError


@dataclass
class BatchSizes:
    preset: Literal['decreased', 'default', 'increased', 'max'] = 'default'
    comments: int | None = None
    replies: int | None = None
    hashtags: int | None = None
    notifications: int | None = None
    posts: int | None = None
    user_posts: int | None = None
    liked_posts: int | None = None
    hashtag_posts: int | None = None
    followers: int | None = None
    following: int | None = None
    blocked: int | None = None

    def __post_init__(self):
        presets = {
            'comments': [50, 100, 200, 500],
            'replies': [20, 100, 100, 100],
            'hashtags': [5, 10, 20, 50],
            'notifications': [10, 20, 50, 1000],
            'posts': [10, 20, 30, 50],
            'user_posts': [10, 20, 30, 50],
            'liked_posts': [10, 20, 30, 50],
            'hashtag_posts': [10, 20, 30, 50],
            'followers': [10, 20, 50, 100],
            'following': [10, 20, 50, 100],
            'blocked': [10, 20, 50, 100]
        }
        presets_map = ['decreased', 'default', 'increased', 'max']
        self._values: dict[str, int] = {}
        for k, v in presets.items():
            if getattr(self, k) is None:
                self._values[k.replace('_', '')] = v[presets_map.index(self.preset)]
            else:
                self._values[k.replace('_', '')] = getattr(self, k)


@dataclass
class Config:
    # для реальных клиентов включен калбэк на ошибки (сами ошибки не выбрасываются) и выключен логгер. Передает ошибки в калбэк, в консоль ничего не пишет, при ошибках сети падает.
    # для ботов включен отлов всех ошибок, а также калбэк при ошибках сети (шоб отправлять в тг например), включен логгер на инфо. Показывает ошибки в консоли, но не завершшает скрипт.
    # для одноразовых скриптов стандартное поведение, отловов ошибок нет, включен логгер на дебаг.
    # ^ это если что просто мысли, не обращайте внимания
    client_type: Literal['client', 'bot', 'onetime'] = 'onetime'

    # enable_logging: bool | None = None
    # logging_level = 'DEBUG'

    is_default: bool = False

    userposts_add_pinned_post: bool = True

    load_on_init: bool = False
    load_on_getattr: bool = True
    auto_load: bool | None = None
    load_on_getitem: int | All | Batch | None = 1
    load_on_iter: int | All | Batch | None = BATCH
    force_load_lists: bool = False  # load lists even if has_more is False

    debug_response: DebugResponseMode = DebugResponseMode.NO

    timeout: float | None = None
    timeout_file: float | None = None
    timeout_file_download: float | None = None

    url: str = 'https://xn--d1ah4a.com/api'
    user_agent: UserAgent | str = UserAgent.BROWSER
    solve_challenge: bool = True

    parse_mode: ParseMode = ParseMode.NO

    retry_enabled: bool | None = None
    retry_delay: float = 10  # delay before next attempt (after rate limit error) if retry_after is not provided in response
    retry_max_retries: int | None = 10  # none for no limit
    retry_exceptions: tuple[type[Exception], ...] | None = None
    retry_max_retry_after: int = 500

    bypass_auth_level: bool = False

    dwell_enabled: bool = True
    dwell_max_buffer: int = 20
    dwell_send_interval: float = 2
    dwell_save_on_quit: bool = True
    dwell_wait_durations: bool = False
    dwell_max_duration: int = 30000
    dwell_min_duration: int = 250
    dwell_check_active: bool | None = None
    dwell_check_active_interval: float = 5
    dwell_inactive_timeout: int = 30
    post_view_increment: bool = False
    post_auto_view: bool = True  # view when called post.set_invisible()

    post_update_stats: bool | None = None
    post_update_stats_interval: int = 3

    captcha_solve: bool = False
    captcha_headless: bool | Literal['virtual'] = 'virtual'

    view_read_speed: int = 250  # in WPM # https://scholarwithin.com/average-reading-speed
    view_images_speed: int = 130  # https://news.mit.edu/2014/in-the-blink-of-an-eye-0116

    on_exceptions: dict[type[Exception], Callable[[Exception], None]] = field(default_factory=dict)
    batch_sizes: BatchSizes = field(default_factory=BatchSizes)
    refresh_token_cookie_name: str = 'refresh_token'

    interactive_auth: bool | None = None

    def __post_init__(self):
        match self.user_agent:
            case UserAgent.DEFAULT:
                self._user_agent = default_user_agent()
            case UserAgent.SDK:
                self._user_agent = get_sdk_user_agent()
            case UserAgent.EMPTY:
                self._user_agent = ''
            case UserAgent.BROWSER:
                self._user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0'
            case _:
                self._user_agent = self.user_agent

        if self.timeout is None:
            match self.client_type:
                case 'onetime':
                    self._timeout = 5
                case 'client':
                    self._timeout = 20
                case 'bot':
                    self._timeout = 60
        else:
            self._timeout = self.timeout

        if self.retry_enabled is None:
            self._retry_enabled = self.client_type == 'bot'
        else:
            self._retry_enabled = self.retry_enabled

        if self.post_update_stats is None:
            self._post_update_stats = self.client_type == 'client'
        else:
            self._post_update_stats = self.post_update_stats

        if self.dwell_check_active is None:
            self._dwell_check_active = self.client_type == 'client'
        else:
            self._dwell_check_active = self.dwell_check_active

        if self.retry_exceptions is None:
            if self.client_type == 'bot':
                self._retry_exceptions = (RateLimitError, RequestException)
            else:
                self._retry_exceptions = ()
        else:
            self._retry_exceptions = self.retry_exceptions

        if self.interactive_auth is None:
            self._interactive_auth = self.client_type != 'client'
        else:
            self._interactive_auth = self.interactive_auth
