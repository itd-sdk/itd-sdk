from uuid import UUID, uuid4
from _io import BufferedReader
from typing import cast, Iterator
from datetime import datetime
from json import JSONDecodeError, loads
from time import sleep
from functools import wraps

from sseclient import SSEClient

from requests import Session
from requests.adapters import HTTPAdapter

from itd.request import fetch
from itd.routes.users import (
    get_user, update_profile, follow, unfollow, get_followers, get_following, update_privacy,
    delete_account, restore_account, block, unblock, get_blocked,
    get_follow_status
)
from itd.routes.etc import get_top_clans, get_who_to_follow
from itd.routes.comments import (
    get_comments, add_comment, delete_comment, like_comment, unlike_comment, add_reply_comment,
    get_replies
)
from itd.routes.hashtags import get_hashtags, get_posts_by_hashtag
from itd.routes.notifications import (
    get_notifications, mark_as_read, mark_all_as_read, get_unread_notifications_count,
    stream_notifications
)
from itd.routes.posts import (
    create_post, get_posts, get_post, edit_post, delete_post, pin_post, repost, view_post,
    get_liked_posts, restore_post, like_post, unlike_post, get_user_posts
)
from itd.routes.reports import report
from itd.routes.search import search
from itd.routes.files import upload_file, get_file, delete_file
from itd.routes.auth import refresh_token, change_password, logout
from itd.routes.verification import verify, get_verification_status
from itd.routes.pins import get_pins, remove_pin, set_pin

from itd.models.comment import Comment
from itd.models.notification import Notification
from itd.models.post import Post, PollData, Poll, Span
from itd.models.clan import Clan
from itd.models.hashtag import Hashtag
from itd.models.user import (
    User, UserProfileUpdate, UserPrivacy, UserFollower, UserWhoToFollow, UserPrivacyData, UserBlock
)
from itd.models.pagination import Pagination, PostsPagintaion, LikedPostsPagintaion, PagePagination
from itd.models.verification import Verification, VerificationStatus
from itd.models.report import NewReport
from itd.models.file import File
from itd.models.pin import Pin
from itd.models.event import StreamConnect, StreamNotification

from itd.enums import PostsTab, ReportTargetType, ReportTargetReason, UserPostSorting, Unset
from itd.request import decode_jwt_payload
from itd.exceptions import (
    NoCookie, NoAuthData, SamePassword, InvalidOldPassword, NotFound, ValidationError,
    PendingRequestExists, Forbidden, UsernameTaken, CantFollowYourself, Unauthorized,
    CantRepostYourPost, AlreadyReposted, AlreadyReported, TooLarge, PinNotOwned,
    AlreadyFollowing, NotFoundOrForbidden, OptionsNotBelong, NotMultipleChoice, EmptyOptions,
    RequiresVerification, InvalidFileType, EditExpired, UploadError,
    AlreadyBlocked, NotBlocked, CantBlockYourself, TargetUserBanned,
    UserBlocked, NotFoundOrBlocked
)
from itd.exceptions import Unauthorized
from itd._default import _default_client, set_default_client
from itd.user import Me


def refresh_on_error(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.refresh_token:
            try:
                return func(self, *args, **kwargs)
            except Unauthorized:
                self.access_token = None # token is expired!
                self.refresh_auth()
                return func(self, *args, **kwargs)
        else:
            return func(self, *args, **kwargs)
    return wrapper


class Client:
    access_token: str | None = None
    refresh_token: str | None = None
    _user = None

    def __init__(self, refresh_token: str | None = None, access_token: str | None = None):
        self._stream_active = False  # Флаг для остановки stream_notifications
        self.session = Session()
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=10, pool_block=False)
        self.session.mount('https://', adapter)

        if access_token:
            self.access_token = access_token.replace('Bearer ', '')

        elif refresh_token:
            self.refresh_token = refresh_token
            self.session.cookies.set('refresh_token', refresh_token, path='/', domain='xn--d1ah4a.com')
            self.refresh_auth()


        if _default_client is None:
            set_default_client(self)

    def request(self, method: str, url: str, params: dict = {}, files: dict[str, tuple[str, BufferedReader | bytes]] = {}):
        """Сделать запрос

        Args:
            method (str): Метод
            url (str): URL
            params (dict, optional): Параметры. Defaults to {}.
            files (dict[str, tuple[str, BufferedReader | bytes]], optional): Файлы. Defaults to {}.
        """
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
        print('refresh token')
        if not self.refresh_token:
            raise NoCookie()

        res = refresh_token(self.session)
        res.raise_for_status()

        self.access_token = res.json()['accessToken']

        assert self.access_token
        return self.access_token


    @refresh_on_error
    def change_password(self, old: str, new: str) -> dict:
        """Смена пароля

        Args:
            old (str): Старый пароль
            new (str): Новый пароль

        Raises:
            NoCookie: Нет cookie
            SamePassword: Одинаковые пароли
            InvalidOldPassword: Старый пароль неверный

        Returns:
            dict: Ответ API `{'message': 'Password changed successfully'}`
        """
        if not self.refresh_token:
            raise NoCookie()

        res = change_password(self, old, new)
        if res.json().get('error', {}).get('code') == 'SAME_PASSWORD':
            raise SamePassword()
        if res.json().get('error', {}).get('code') == 'INVALID_OLD_PASSWORD':
            raise InvalidOldPassword()
        res.raise_for_status()

        return res.json()

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
            self._user = Me()
        return self._user


    @refresh_on_error
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

    @refresh_on_error
    def get_user(self, username: str) -> User:
        """Получить пользователя

        Args:
            username (str): username или "me"

        Raises:
            NotFound: Пользователь не найден
            UserBanned: Пользователь заблокирован

        Returns:
            User: Пользователь
        """
        res = get_user(self, username)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        if res.json().get('error', {}).get('message') == 'Этот аккаунт заблокирован':
            raise TargetUserBanned()
        if res.json().get('error', {}).get('code') == 'USER_BLOCKED':
            raise UserBlocked()
        res.raise_for_status()

        return User.model_validate(res.json())

    @refresh_on_error
    def get_me(self) -> User:
        """Получить текущего пользователя (me)

        Returns:
            User: Пользователь
        """
        return self.get_user('me')

    @refresh_on_error
    def update_profile(self, username: str | None = None, display_name: str | None = None, bio: str | None = None, banner_id: UUID | Unset | None = None) -> UserProfileUpdate:
        """Обновить профиль

        Args:
            username (str | None, optional): username. Defaults to None.
            display_name (str | None, optional): Отображаемое имя. Defaults to None.
            bio (str | None, optional): Биография (о себе). Defaults to None.
            banner_id (UUID | Unset | None, optional): UUID баннера. Defaults to None.

        Raises:
            ValidationError: Ошибка валидации
            InvalidFileType: Баннер может быть только изображением

        Returns:
            UserProfileUpdate: Обновленный профиль
        """
        res = update_profile(self, bio, display_name, username, banner_id)
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        if res.json().get('error', {}).get('message') == 'Баннер может быть только изображением':
            raise InvalidFileType()
        if res.json().get('error', {}).get('code') == 'GIF_REQUIRES_VERIFICATION':
            raise RequiresVerification('GIF banner')
        if res.json().get('error', {}).get('code') == 'USERNAME_TAKEN':
            raise UsernameTaken()
        res.raise_for_status()

        return UserProfileUpdate.model_validate(res.json())


    @refresh_on_error
    def follow(self, username: str) -> int:
        """Подписаться на пользователя

        Args:
            username (str): username

        Raises:
            NotFound: Пользователь не найден
            CantFollowYourself: Невозможно подписаться на самого себе

        Returns:
            int: Число подписчиков после подписки
        """
        res = follow(self, username)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        if res.json().get('error', {}).get('code') == 'CONFLICT':
            raise AlreadyFollowing()
        if res.json().get('error', {}).get('message') == 'Cannot follow yourself':
            raise CantFollowYourself()
        if res.json().get('error', {}).get('code') == 'BLOCKED':
            raise UserBlocked()
        if res.json().get('error', {}).get('message') == 'Этот аккаунт заблокирован':
            raise TargetUserBanned()
        res.raise_for_status()

        return res.json()['followersCount']

    @refresh_on_error
    def unfollow(self, username: str) -> int:
        """Отписаться от пользователя

        Args:
            username (str): username

        Raises:
            NotFound: Пользователь не найден

        Returns:
            int: Число подписчиков после отписки
        """
        res = unfollow(self, username)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        if res.json().get('error', {}).get('message') == 'Этот аккаунт заблокирован':
            raise TargetUserBanned()
        res.raise_for_status()

        return res.json()['followersCount']

    @refresh_on_error
    def get_followers(self, username: str, page: int = 1) -> tuple[list[UserFollower], Pagination]:
        """Получить подписчиков пользователя

        Args:
            username (str): username
            limit (int, optional): Лимит. Defaults to 30.
            page (int, optional): Страница (при дозагрузке, увеличивайте на 1). Defaults to 1.

        Raises:
            NotFound: Пользователь не найден
            TargetUserBanned: Пользователь заблокирован

        Returns:
            list[UserFollower]: Список подписчиков
            Pagination: Данные пагинации (лимит, страница, сколько всего, есть ли еще)
        """
        res = get_followers(self, username, page)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFoundOrBlocked('User')
        if res.json().get('error', {}).get('message') == 'Этот аккаунт заблокирован':
            raise TargetUserBanned()
        res.raise_for_status()

        return [UserFollower.model_validate(user) for user in res.json()['data']['users']], Pagination.model_validate(res.json()['data']['pagination'])

    @refresh_on_error
    def get_following(self, username: str, page: int = 1) -> tuple[list[UserFollower], Pagination]:
        """Получить подписки пользователя

        Args:
            username (str): username
            limit (int, optional): Лимит. Defaults to 30.
            page (int, optional): Страница (при дозагрузке, увеличивайте на 1). Defaults to 1.

        Raises:
            NotFound: Пользователь не найден

        Returns:
            list[UserFollower]: Список подписок
            Pagination: Данные пагинации (лимит, страница, сколько всего, есть ли еще)
        """
        res = get_following(self, username, page)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFoundOrBlocked('User')
        if res.json().get('error', {}).get('message') == 'Этот аккаунт заблокирован':
            raise TargetUserBanned()
        res.raise_for_status()

        return [UserFollower.model_validate(user) for user in res.json()['data']['users']], Pagination.model_validate(res.json()['data']['pagination'])

    @refresh_on_error
    def block(self, username_or_id: str | UUID):
        """Заблокировать пользователя

        Args:
            username_or_id (str | UUID): username или ID пользователя

        Raises:
            AlreadyBlocked: Пользователь уже заблокирован
            NotFound: Пользователь не найден
            CantBlockYourself: Невозможно заблокировать самого себя
        """
        res = block(self, username_or_id)
        if res.json().get('error', {}).get('code') == 'CONFLICT':
            raise AlreadyBlocked()
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        if res.json().get('error', {}).get('message') == 'Cannot block yourself':
            raise CantBlockYourself()
        if res.json().get('error', {}).get('message') == 'Этот аккаунт заблокирован':
            raise TargetUserBanned()
        res.raise_for_status()

    @refresh_on_error
    def unblock(self, username_or_id: str | UUID):
        """Разблокировать пользователя

        Args:
            username_or_id (str | UUID): username или ID пользователя

        Raises:
            NotBlocked: Пользователь итак не заблокирован
            NotFound: Пользователь не найден.
        """
        res = unblock(self, username_or_id)
        if res.json().get('error', {}).get('code') == 'CONFLICT':
            raise NotBlocked()
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        if res.json().get('error', {}).get('message') == 'Этот аккаунт заблокирован':
            raise TargetUserBanned()
        res.raise_for_status()

    @refresh_on_error
    def get_blocked(self, limit: int = 20, page: int = 1) -> tuple[list[UserBlock], PagePagination]:
        """Получить список заблокированных пользователей

        Args:
            limit (int, optional): Лимит. Defaults to 20.
            page (int, optional): Страница. Defaults to 1.

        Returns:
            list[UserBlock]: Список пользователей
            PagePagination: Пагинация
        """
        res = get_blocked(self, limit, page)
        res.raise_for_status()

        data = res.json()['data']
        return [UserBlock.model_validate(user) for user in data['users']], PagePagination.model_validate(data['pagination'])

    @refresh_on_error
    def get_follow_status(self, user_ids: list[UUID]) -> dict[UUID, bool]:
        """Получить статус подписки (подписаны ли вы на пользователей)

        Args:
            user_ids (list[UUID]): Список пользователей для проверки

        Returns:
            dict[UUID, bool]: Словарь пользователей, где значение - полписаны вы или нет
        """
        res = get_follow_status(self, user_ids)
        res.raise_for_status()

        return {UUID(k): v for k, v in res.json()['data'].items()}

    @refresh_on_error
    def verify(self, file_url: str) -> Verification:
        """Отправить запрос на верификацию

        Args:
            file_url (str): Ссылка на видео

        Raises:
            PendingRequestExists: Запрос уже отправлен

        Returns:
            Verification: Верификация
        """
        res = verify(self, file_url)
        if res.json().get('error', {}).get('code') == 'PENDING_REQUEST_EXISTS':
            raise PendingRequestExists()
        res.raise_for_status()

        return Verification.model_validate(res.json())

    @refresh_on_error
    def get_verification_status(self) -> VerificationStatus:
        """Получить статус верификации

        Returns:
            VerificationStatus: Верификация
        """
        res = get_verification_status(self)
        res.raise_for_status()

        return VerificationStatus.model_validate(res.json())

    @refresh_on_error
    def get_who_to_follow(self) -> list[UserWhoToFollow]:
        """Получить список популярных пользователей (кого читать)

        Returns:
            list[UserWhoToFollow]: Список пользователей
        """
        res = get_who_to_follow(self)
        res.raise_for_status()

        return [UserWhoToFollow.model_validate(user) for user in res.json()['users']]

    @refresh_on_error
    def get_top_clans(self) -> list[Clan]:
        """Получить топ кланов

        Returns:
            list[Clan]: Топ кланов
        """
        res = get_top_clans(self)
        res.raise_for_status()

        return [Clan.model_validate(clan) for clan in res.json()['clans']]

    @refresh_on_error
    def get_hashtags(self, limit: int = 10) -> list[Hashtag]:
        """Получить список популярных хэштэгов

        Args:
            limit (int, optional): Лимит. Defaults to 10.

        Returns:
            list[Hashtag]: Список хэштэгов
        """
        res = get_hashtags(self, limit)
        res.raise_for_status()

        return [Hashtag.model_validate(hashtag) for hashtag in res.json()['data']['hashtags']]

    @refresh_on_error
    def get_posts_by_hashtag(self, hashtag: str, limit: int = 20, cursor: UUID | None = None) -> tuple[Hashtag | None, list[Post], Pagination]:
        """Получить посты по хэштэгу

        Args:
            hashtag (str): Хэштэг (без #)
            limit (int, optional): Лимит. Defaults to 20.
            cursor (UUID | None, optional): Курсор (UUID последнего поста, после которого брать данные). Defaults to None.

        Returns:
            Hashtag | None: Хэштэг
            list[Post]: Посты
            Pagination: Пагинация
        """
        res = get_posts_by_hashtag(self, hashtag, limit, cursor)
        res.raise_for_status()
        data = res.json()['data']

        return Hashtag.model_validate(data['hashtag']), [Post.model_validate(post) for post in data['posts']], Pagination.model_validate(data['pagination'])


    @refresh_on_error
    def get_notifications(self, limit: int = 20, offset: int = 0) -> tuple[list[Notification], Pagination]:
        """Получить уведомления

        Args:
            limit (int, optional): Лимит. Defaults to 20.
            offset (int, optional): Сдвиг. Defaults to 0.

        Returns:
            list[Notification]: Уведомления
            Pagination: Пагинация
        """
        res = get_notifications(self, limit, offset)
        res.raise_for_status()

        return (
            [Notification.model_validate(notification) for notification in res.json()['notifications']],
            Pagination(page=(offset // limit) + 1, limit=limit, hasMore=res.json()['hasMore'], nextCursor=None)
        )

    @refresh_on_error
    def mark_as_read(self, id: UUID) -> bool:
        """Прочитать уведомление

        Args:
            id (UUID): UUID уведомления

        Returns:
            bool: Успешно (False - уже прочитано)
        """
        res = mark_as_read(self, id)
        res.raise_for_status()

        return res.json()['success']

    @refresh_on_error
    def mark_all_as_read(self) -> None:
        """Прочитать все уведомления"""
        res = mark_all_as_read(self)
        res.raise_for_status()

    @refresh_on_error
    def get_unread_notifications_count(self) -> int:
        """Получить количество непрочитанных уведомлений

        Returns:
            int: Количество
        """
        res = get_unread_notifications_count(self)
        res.raise_for_status()

        return res.json()['count']

    @refresh_on_error
    def get_user_posts(self, username_or_id: str | UUID, limit: int = 20, cursor: datetime | None = None, pinned_post_id: UUID | None = None, sort: UserPostSorting = UserPostSorting.NEW) -> tuple[list[Post], LikedPostsPagintaion]:
        """Получить список постов пользователя

        Args:
            username_or_id (str | UUID): UUID или username пользователя
            limit (int, optional): Лимит. Defaults to 20.
            cursor (datetime | None, optional): Сдвиг (next_cursor). Defaults to None.
            pinned_post_id (UUID | None, optional): UUID закрепленного поста. Defaults to None.
            sort (UserPostSorting | None, optional): Сортировка. Defaults to UserPostSorting.NEW.

        Raises:
            NotFound: Пользователь не найден

        Returns:
            list[Post]: Список постов
            LikedPostsPagintaion: Пагинация
        """
        res = get_user_posts(self, username_or_id, limit, cursor, pinned_post_id, sort)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        res.raise_for_status()
        data = res.json()['data']

        return [Post.model_validate(post) for post in data['posts']], LikedPostsPagintaion.model_validate(data['pagination'])

    @refresh_on_error
    def get_liked_posts(self, username_or_id: str | UUID, limit: int = 20, cursor: datetime | None = None) -> tuple[list[Post], LikedPostsPagintaion]:
        """Получить список лайкнутых постов пользователя

        Args:
            username_or_id (str | UUID): UUID или username пользователя
            limit (int, optional): Лимит. Defaults to 20.
            cursor (datetime | None, optional): Сдвиг (next_cursor). Defaults to None.

        Raises:
            NotFound: Пользователь не найден

        Returns:
            list[Post]: Список постов
            LikedPostsPagintaion: Пагинация
        """
        res = get_liked_posts(self, username_or_id, limit, cursor)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        res.raise_for_status()
        data = res.json()['data']

        return [Post.model_validate(post) for post in data['posts']], LikedPostsPagintaion.model_validate(data['pagination'])


    @refresh_on_error
    def report(self, id: UUID, type: ReportTargetType = ReportTargetType.POST, reason: ReportTargetReason = ReportTargetReason.OTHER, description: str | None = None) -> NewReport:
        """Отправить жалобу

        Args:
            id (UUID): UUID цели
            type (ReportTargetType, optional): Тип цели (пост/пользователь/комментарий). Defaults to ReportTargetType.POST.
            reason (ReportTargetReason, optional): Причина. Defaults to ReportTargetReason.OTHER.
            description (str | None, optional): Описание. Defaults to None.

        Raises:
            NotFound: Цель не найдена
            AlreadyReported: Жалоба уже отправлена
            ValidationError: Ошибка валидации

        Returns:
            NewReport: Новая жалоба
        """
        res = report(self, id, type, reason, description)

        if res.json().get('error', {}).get('code') == 'VALIDATION_ERROR' and 'не найден' in res.json()['error'].get('message', ''):
            raise NotFound(type.value.title())
        if res.json().get('error', {}).get('code') == 'VALIDATION_ERROR' and 'Вы уже отправляли жалобу' in res.json()['error'].get('message', ''):
            raise AlreadyReported(type.value.title())
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[-1])
        res.raise_for_status()

        return NewReport.model_validate(res.json()['data'])


    @refresh_on_error
    def search(self, query: str, user_limit: int = 5, hashtag_limit: int = 5) -> tuple[list[UserWhoToFollow], list[Hashtag]]:
        """Поиск по пользователям и хэштэгам

        Args:
            query (str): Запрос
            user_limit (int, optional): Лимит пользователей. Defaults to 5.
            hashtag_limit (int, optional): Лимит хэштэгов. Defaults to 5.

        Raises:
            TooLarge: Слишком длинный запрос

        Returns:
            list[UserWhoToFollow]: Список пользователей
            list[Hashtag]: Список хэштэгов
        """
        res = search(self, query, user_limit, hashtag_limit)

        if res.status_code == 414:
            raise TooLarge('Query')
        res.raise_for_status()
        data = res.json()['data']

        return [UserWhoToFollow.model_validate(user) for user in data['users']], [Hashtag.model_validate(hashtag) for hashtag in data['hashtags']]

    @refresh_on_error
    def search_user(self, query: str, limit: int = 5) -> list[UserWhoToFollow]:
        """Поиск пользователей

        Args:
            query (str): Запрос
            limit (int, optional): Лимит. Defaults to 5.

        Returns:
            list[UserWhoToFollow]: Список пользователей
        """
        return self.search(query, limit, 0)[0]

    @refresh_on_error
    def search_hashtag(self, query: str, limit: int = 5) -> list[Hashtag]:
        """Поиск хэштэгов

        Args:
            query (str): Запрос
            limit (int, optional): Лимит. Defaults to 5.

        Returns:
            list[Hashtag]: Список хэштэгов
        """
        return self.search(query, 0, limit)[1]


    @refresh_on_error
    def upload_file(self, name: str, data: BufferedReader | bytes) -> File:
        """Загрузить файл

        Args:
            name (str): Имя файла
            data (BufferedReader): Содержимое (open('имя', 'rb'))

        Raises:
            TooLarge: Слишком большой файл
            InvalidFileType: Неправильный тип файла
            UploadError: Ошибка загрузки файла

        Returns:
            File: Файл
        """
        res = upload_file(self, name, data)
        if res.status_code == 413:
            raise TooLarge('File')
        if res.json().get('error', {}).get('message') == 'Недопустимый тип файла':
            raise InvalidFileType()
        if res.json().get('error', {}).get('code') == 'UPLOAD_ERROR':
            raise UploadError()
        res.raise_for_status()

        return File.model_validate(res.json())

    @refresh_on_error
    def get_file(self, id: UUID) -> File:
        """Получить файл

        Args:
            id (UUID): UUID файла

        Raises:
            NotFoundOrForbidden: Файл не найден или нет доступа

        Returns:
            File: Файл
        """
        res = get_file(self, id)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFoundOrForbidden('File')
        res.raise_for_status()

        return File.model_validate(res.json())

    @refresh_on_error
    def delete_file(self, id: UUID) -> File:
        """Удалить файл

        Args:
            id (UUID): UUID файла

        Raises:
            NotFound: Файл не найден
        """
        res = delete_file(self, id)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('File')
        res.raise_for_status()

        return File.model_validate(res.json())

    # @deprecated # Этот декоратор появился в 3.13, а наша библиотека поддерживает с 3.9
    def update_banner(self, name: str) -> UserProfileUpdate:
        """[DEPRECATED] Обновить банер (шорткат из upload_file + update_profile)

        Args:
            name (str): Имя файла

        Returns:
            UserProfileUpdate: Обновленный профиль
        """
        id = self.upload_file(name, cast(BufferedReader, open(name, 'rb'))).id
        return self.update_profile(banner_id=id)

    def update_banner_new(self, name: str) -> tuple[File, UserProfileUpdate]:
        """Обновить банер (шорткат из upload_file + update_profile)

        Args:
            name (str): Имя файла

        Returns:
            File: Загруженный файл
            UserProfileUpdate: Обновленный профиль
        """
        file = self.upload_file(name, cast(BufferedReader, open(name, 'rb')))
        return file, self.update_profile(banner_id=file.id)


    @refresh_on_error
    def get_pins(self) -> tuple[list[Pin], str]:
        """Список пинов

        Returns:
            list[Pin]: Список пинов
            str: Активный пин
        """
        res = get_pins(self)
        res.raise_for_status()
        data = res.json()['data']

        return [Pin.model_validate(pin) for pin in data['pins']], data['activePin']

    @refresh_on_error
    def remove_pin(self):
        """Снять пин"""
        res = remove_pin(self)
        res.raise_for_status()

    @refresh_on_error
    def set_pin(self, slug: str):
        res = set_pin(self, slug)
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        if res.json().get('error', {}).get('code') == 'PIN_NOT_OWNED':
            raise PinNotOwned(slug)
        res.raise_for_status()

        return res.json()['pin']

    @refresh_on_error
    def stream_notifications(self) -> Iterator[StreamConnect | StreamNotification]:
        """Слушать SSE поток уведомлений

        Yields:
            StreamConnect | StreamNotification: События подключения или уведомления

        Example:
            ```python
            from itd import ITDClient

            client = ITDClient(cookies='refresh_token=...')

            # Запуск прослушивания
            for event in client.stream_notifications():
                if isinstance(event, StreamConnect):
                    print(f'Подключено: {event.user_id}')
                else:
                    print(f'Уведомление: {event.type} от {event.actor.username}')

            # Остановка из другого потока или обработчика
            # client.stop_stream()
            ```
        """
        self._stream_active = True

        while self._stream_active:
            try:
                response = stream_notifications(self)
                response.raise_for_status()

                client = SSEClient(response)

                for event in client.events():
                    if not self._stream_active:
                        response.close()
                        return

                    try:
                        if not event.data or event.data.strip() == '':
                            continue

                        data = loads(event.data)

                        if 'userId' in data and 'timestamp' in data and 'type' not in data:
                            yield StreamConnect.model_validate(data)
                        else:
                            yield StreamNotification.model_validate(data)

                    except JSONDecodeError:
                        print(f'Не удалось распарсить сообщение: {event.data}')
                        continue
                    except Exception as e:
                        print(f'Ошибка обработки события: {e}')
                        continue

            except Unauthorized:
                if self.cookies and self._stream_active:
                    print('Токен истек, обновляем...')
                    self.refresh_auth()
                    continue
                else:
                    raise
            except Exception as e:
                if not self._stream_active:
                    return
                print(f'Ошибка соединения: {e}, переподключение через 5 секунд...')
                sleep(5)
                continue

    def stop_stream(self):
        """Остановить прослушивание SSE потока

        Example:
            ```python
            import threading
            from itd import ITDClient

            client = ITDClient(cookies='refresh_token=...')

            # Запуск в отдельном потоке
            def listen():
                for event in client.stream_notifications():
                    print(event)

            thread = threading.Thread(target=listen)
            thread.start()

            # Остановка через 10 секунд
            import time
            time.sleep(10)
            client.stop_stream()
            thread.join()
            ```
        """
        print('stop event')
        self._stream_active = False
