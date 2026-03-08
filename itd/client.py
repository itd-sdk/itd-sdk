from warnings import deprecated
from uuid import UUID
from _io import BufferedReader
from typing import cast
from datetime import datetime

from requests.exceptions import ConnectionError, HTTPError

from itd.routes.users import get_user, update_profile, follow, unfollow, get_followers, get_following, update_privacy
from itd.routes.etc import get_top_clans, get_who_to_follow, get_platform_status
from itd.routes.comments import get_comments, add_comment, delete_comment, like_comment, unlike_comment, add_reply_comment
from itd.routes.hashtags import get_hashtags, get_posts_by_hashtag
from itd.routes.notifications import get_notifications, mark_as_read, mark_all_as_read, get_unread_notifications_count
from itd.routes.posts import create_post, get_posts, get_post, edit_post, delete_post, pin_post, repost, view_post, get_liked_posts, restore_post, like_post, unlike_post
from itd.routes.reports import report
from itd.routes.search import search
from itd.routes.files import upload_file
from itd.routes.auth import refresh_token, change_password, logout
from itd.routes.verification import verify, get_verification_status
from itd.routes.pins import get_pins, remove_pin, set_pin

from itd.models.comment import Comment
from itd.models.notification import Notification
from itd.models.post import Post, NewPost
from itd.models.clan import Clan
from itd.models.hashtag import Hashtag
from itd.models.user import User, UserProfileUpdate, UserPrivacy, UserFollower, UserWhoToFollow
from itd.models.pagination import Pagination, PostsPagintaion, LikedPostsPagintaion
from itd.models.verification import Verification, VerificationStatus
from itd.models.report import NewReport
from itd.models.file import File
from itd.models.pin import Pin

from itd.enums import PostsTab, ReportTargetType, ReportTargetReason
from itd.request import set_cookies
from itd.exceptions import (
    NoCookie, NoAuthData, SamePassword, InvalidOldPassword, NotFound, ValidationError, UserBanned,
    PendingRequestExists, Forbidden, UsernameTaken, CantFollowYourself, Unauthorized,
    CantRepostYourPost, AlreadyReposted, AlreadyReported, TooLarge, PinNotOwned
)


def refresh_on_error(func):
    def wrapper(self, *args, **kwargs):
        if self.cookies:
            try:
                return func(self, *args, **kwargs)
            except (Unauthorized, ConnectionError, HTTPError):
                self.refresh_auth()
                return func(self, *args, **kwargs)
        else:
            return func(self, *args, **kwargs)
    return wrapper


class Client:
    def __init__(self, token: str | None = None, cookies: str | None = None):
        self.cookies = cookies

        if token:
            self.token = token.replace('Bearer ', '')
        elif self.cookies:
            set_cookies(self.cookies)
            self.refresh_auth()
        else:
            raise NoAuthData()

    def refresh_auth(self) -> str:
        """Обновить access token

        Raises:
            NoCookie: Нет cookie

        Returns:
            str: Токен
        """
        print('refresh token')
        if not self.cookies:
            raise NoCookie()

        res = refresh_token(self.cookies)
        res.raise_for_status()

        self.token = res.json()['accessToken']
        return self.token

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
        if not self.cookies:
            raise NoCookie()

        res = change_password(self.cookies, self.token, old, new)
        if res.json().get('error', {}).get('code') == 'SAME_PASSWORD':
            raise SamePassword()
        if res.json().get('error', {}).get('code') == 'INVALID_OLD_PASSWORD':
            raise InvalidOldPassword()
        res.raise_for_status()

        return res.json()

    @refresh_on_error
    def logout(self) -> dict:
        """Выход из аккаунта

        Raises:
            NoCookie: Нет cookie

        Returns:
            dict: Ответ API
        """
        if not self.cookies:
            raise NoCookie()

        res = logout(self.cookies)
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
        res = get_user(self.token, username)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        if res.json().get('error', {}).get('code') == 'USER_BLOCKED':
            raise UserBanned()
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
    def update_profile(self, username: str | None = None, display_name: str | None = None, bio: str | None = None, banner_id: UUID | None = None) -> UserProfileUpdate:
        """Обновить профиль

        Args:
            username (str | None, optional): username. Defaults to None.
            display_name (str | None, optional): Отображаемое имя. Defaults to None.
            bio (str | None, optional): Биография (о себе). Defaults to None.
            banner_id (UUID | None, optional): UUID баннера. Defaults to None.

        Raises:
            ValidationError: Ошибка валидации

        Returns:
            UserProfileUpdate: Обновленный профиль
        """
        res = update_profile(self.token, bio, display_name, username, banner_id)
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        if res.json().get('error', {}).get('code') == 'USERNAME_TAKEN':
            raise UsernameTaken()
        res.raise_for_status()

        return UserProfileUpdate.model_validate(res.json())

    @refresh_on_error
    def update_privacy(self, wall_closed: bool = False, private: bool = False) -> UserPrivacy:
        """Обновить настройки приватности

        Args:
            wall_closed (bool, optional): Закрыть стену. Defaults to False.
            private (bool, optional): Приватность. На данный момент неизвестно, что делает этот параметр. Defaults to False.

        Returns:
            UserPrivacy: Обновленные данные приватности
        """
        res = update_privacy(self.token, wall_closed, private)
        res.raise_for_status()

        return UserPrivacy.model_validate(res.json())

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
        res = follow(self.token, username)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        if res.json().get('error', {}).get('code') == 'VALIDATION_ERROR' and res.status_code == 400:
            raise CantFollowYourself()
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
        res = unfollow(self.token, username)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        res.raise_for_status()

        return res.json()['followersCount']

    @refresh_on_error
    def get_followers(self, username: str, limit: int = 30, page: int = 1) -> tuple[list[UserFollower], Pagination]:
        """Получить подписчиков пользователя

        Args:
            username (str): username
            limit (int, optional): Лимит. Defaults to 30.
            page (int, optional): Страница (при дозагрузке, увеличивайте на 1). Defaults to 1.

        Raises:
            NotFound: Пользователь не найден

        Returns:
            list[UserFollower]: Список подписчиков
            Pagination: Данные пагинации (лимит, страница, сколько всего, есть ли еще)
        """
        res = get_followers(self.token, username, limit, page)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        res.raise_for_status()

        return [UserFollower.model_validate(user) for user in res.json()['data']['users']], Pagination.model_validate(res.json()['data']['pagination'])

    @refresh_on_error
    def get_following(self, username: str, limit: int = 30, page: int = 1) -> tuple[list[UserFollower], Pagination]:
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
        res = get_following(self.token, username, limit, page)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('User')
        res.raise_for_status()

        return [UserFollower.model_validate(user) for user in res.json()['data']['users']], Pagination.model_validate(res.json()['data']['pagination'])

    @deprecated("verificate устарел используйте verify")
    @refresh_on_error
    def verificate(self, file_url: str) -> Verification:
        """Отправить запрос на верификацию

        Args:
            file_url (str): Ссылка на видео

        Raises:
            PendingRequestExists: Запрос уже отправлен

        Returns:
            Verification: Верификация
        """
        return self.verify(file_url)

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
        res = verify(self.token, file_url)
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
        res = get_verification_status(self.token)
        res.raise_for_status()

        return VerificationStatus.model_validate(res.json())

    @refresh_on_error
    def get_who_to_follow(self) -> list[UserWhoToFollow]:
        """Получить список популярных пользователей (кого читать)

        Returns:
            list[UserWhoToFollow]: Список пользователей
        """
        res = get_who_to_follow(self.token)
        res.raise_for_status()

        return [UserWhoToFollow.model_validate(user) for user in res.json()['users']]

    @refresh_on_error
    def get_top_clans(self) -> list[Clan]:
        """Получить топ кланов

        Returns:
            list[Clan]: Топ кланов
        """
        res = get_top_clans(self.token)
        res.raise_for_status()

        return [Clan.model_validate(clan) for clan in res.json()['clans']]

    @refresh_on_error
    def get_platform_status(self) -> bool:
        """Получить статус платформы

        Returns:
            bool: read only
        """
        res = get_platform_status(self.token)
        res.raise_for_status()

        return res.json()['readOnly']


    @refresh_on_error
    def add_comment(self, post_id: UUID, content: str, attachment_ids: list[UUID] = []) -> Comment:
        """Добавить комментарий

        Args:
            post_id (str): UUID поста
            content (str): Содержание
            attachment_ids (list[UUID]): Список UUID прикреплённых файлов
            reply_comment_id (UUID | None, optional): ID коммента для ответа. Defaults to None.

        Raises:
            ValidationError: Ошибка валидации
            NotFound: Пост не найден

        Returns:
            Comment: Комментарий
        """
        res = add_comment(self.token, post_id, content, attachment_ids)
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Post')
        res.raise_for_status()

        return Comment.model_validate(res.json())


    @refresh_on_error
    def add_reply_comment(self, comment_id: UUID, content: str, author_id: UUID, attachment_ids: list[UUID] = []) -> Comment:
        """Добавить ответный комментарий

        Args:
            comment_id (str): UUID комментария
            content (str): Содержание
            author_id (UUID | None, optional): ID пользователя, отправившего комментарий. Defaults to None.
            attachment_ids (list[UUID]): Список UUID прикреплённых файлов

        Raises:
            ValidationError: Ошибка валидации
            NotFound: Пользователь или комментарий не найден

        Returns:
            Comment: Комментарий
        """
        res = add_reply_comment(self.token, comment_id, content, author_id, attachment_ids)
        if res.status_code == 500 and 'Failed query' in res.text:
            raise NotFound('User')
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Comment')
        res.raise_for_status()

        return Comment.model_validate(res.json())


    @refresh_on_error
    def get_comments(self, post_id: UUID, limit: int = 20, cursor: int = 0, sort: str = 'popular') -> tuple[list[Comment], Pagination]:
        """Получить список комментариев

        Args:
            post_id (UUID): UUID поста
            limit (int, optional): Лимит. Defaults to 20.
            cursor (int, optional): Курсор (сколько пропустить). Defaults to 0.
            sort (str, optional): Сортировка. Defaults to 'popular'.

        Raises:
            NotFound: Пост не найден

        Returns:
            list[Comment]: Список комментариев
            Pagination: Пагинация
        """
        res = get_comments(self.token, post_id, limit, cursor, sort)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Post')
        res.raise_for_status()
        data = res.json()['data']

        return [Comment.model_validate(comment) for comment in data['comments']], Pagination(page=(cursor // limit) or 1, limit=limit, total=data['total'], hasMore=data['hasMore'], nextCursor=None)

    @refresh_on_error
    def like_comment(self, id: UUID) -> int:
        """Лайкнуть комментарий

        Args:
            id (UUID): UUID комментария

        Raises:
            NotFound: Комментарий не найден

        Returns:
            int: Количество лайков
        """
        res = like_comment(self.token, id)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Comment')
        res.raise_for_status()

        return res.json()['likesCount']

    @refresh_on_error
    def unlike_comment(self, id: UUID) -> int:
        """Убрать лайк с комментария

        Args:
            id (UUID): UUID комментария

        Raises:
            NotFound: Комментарий не найден

        Returns:
            int: Количество лайков
        """
        res = unlike_comment(self.token, id)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Comment')
        res.raise_for_status()

        return res.json()['likesCount']

    @refresh_on_error
    def delete_comment(self, id: UUID) -> None:
        """Удалить комментарий

        Args:
            id (UUID): UUID комментария

        Raises:
            NotFound: Комментарий не найден
            Forbidden: Нет прав на удаление
        """
        res = delete_comment(self.token, id)
        if res.status_code == 204:
            return
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Comment')
        if res.json().get('error', {}).get('code') == 'FORBIDDEN':
            raise Forbidden('delete comment')
        res.raise_for_status()

    @deprecated("get_hastags устарел используйте get_hashtags")
    @refresh_on_error
    def get_hastags(self, limit: int = 10) -> list[Hashtag]:
        """Получить список популярных хэштэгов

        Args:
            limit (int, optional): Лимит. Defaults to 10.

        Returns:
            list[Hashtag]: Список хэштэгов
        """
        return self.get_hashtags(limit)

    @refresh_on_error
    def get_hashtags(self, limit: int = 10) -> list[Hashtag]:
        """Получить список популярных хэштэгов

        Args:
            limit (int, optional): Лимит. Defaults to 10.

        Returns:
            list[Hashtag]: Список хэштэгов
        """
        res = get_hashtags(self.token, limit)
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
        res = get_posts_by_hashtag(self.token, hashtag, limit, cursor)
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
        res = get_notifications(self.token, limit, offset)
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
        res = mark_as_read(self.token, id)
        res.raise_for_status()

        return res.json()['success']

    @refresh_on_error
    def mark_all_as_read(self) -> None:
        """Прочитать все уведомления"""
        res = mark_all_as_read(self.token)
        res.raise_for_status()


    @refresh_on_error
    def get_unread_notifications_count(self) -> int:
        """Получить количество непрочитанных уведомлений

        Returns:
            int: Количество
        """
        res = get_unread_notifications_count(self.token)
        res.raise_for_status()

        return res.json()['count']


    @refresh_on_error
    def create_post(self, content: str, wall_recipient_id: UUID | None = None, attach_ids: list[UUID] = []) -> NewPost:
        """Создать пост

        Args:
            content (str): Содержимое
            wall_recipient_id (UUID | None, optional): UUID пользователя (чтобы создать пост ему на стене). Defaults to None.
            attach_ids (list[UUID], optional): UUID вложений. Defaults to [].

        Raises:
            NotFound: Пользователь не найден
            ValidationError: Ошибка валидации

        Returns:
            NewPost: Новый пост
        """
        res = create_post(self.token, content, wall_recipient_id, attach_ids)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Wall recipient')
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        res.raise_for_status()

        return NewPost.model_validate(res.json())

    @refresh_on_error
    def get_posts(self, cursor: int = 0, tab: PostsTab = PostsTab.POPULAR) -> tuple[list[Post], PostsPagintaion]:
        """Получить список постов

        Args:
            cursor (int, optional): Страница. Defaults to 0.
            tab (PostsTab, optional): Вкладка (популярное или подписки). Defaults to PostsTab.POPULAR.

        Returns:
            list[Post]: Список постов
            Pagination: Пагинация
        """
        res = get_posts(self.token, cursor, tab)
        res.raise_for_status()
        data = res.json()['data']

        return [Post.model_validate(post) for post in data['posts']], PostsPagintaion.model_validate(data['pagination'])

    @refresh_on_error
    def get_post(self, id: UUID) -> Post:
        """Получить пост

        Args:
            id (UUID): UUID поста

        Raises:
            NotFound: Пост не найден

        Returns:
            Post: Пост
        """
        res = get_post(self.token, id)
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Post')
        res.raise_for_status()

        return Post.model_validate(res.json()['data'])

    @refresh_on_error
    def edit_post(self, id: UUID, content: str) -> str:
        """Редактировать пост

        Args:
            id (UUID): UUID поста
            content (str): Содержимое

        Raises:
            NotFound: Пост не найден
            Forbidden: Нет доступа
            ValidationError: Ошибка валидации

        Returns:
            str: Новое содержимое
        """
        res = edit_post(self.token, id, content)

        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Post')
        if res.json().get('error', {}).get('code') == 'FORBIDDEN':
            raise Forbidden('edit post')
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        res.raise_for_status()

        return res.json()['content']

    @refresh_on_error
    def delete_post(self, id: UUID) -> None:
        """Удалить пост

        Args:
            id (UUID): UUID поста

        Raises:
            NotFound: Пост не найден
            Forbidden: Нет доступа
        """
        res = delete_post(self.token, id)
        if res.status_code == 204:
            return

        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Post')
        if res.json().get('error', {}).get('code') == 'FORBIDDEN':
            raise Forbidden('delete post')
        res.raise_for_status()

    @refresh_on_error
    def pin_post(self, id: UUID):
        """Закрепить пост

        Args:
            id (UUID): UUID поста

        Raises:
            NotFound: Пост не найден
            Forbidden: Нет доступа
        """
        res = pin_post(self.token, id)

        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Post')
        if res.json().get('error', {}).get('code') == 'FORBIDDEN':
            raise Forbidden('pin post')
        res.raise_for_status()

    @refresh_on_error
    def repost(self, id: UUID, content: str | None = None) -> NewPost:
        """Репостнуть пост

        Args:
            id (UUID): UUID поста
            content (str | None, optional): Содержимое (доп. комментарий). Defaults to None.

        Raises:
            NotFound: Пост не найден
            AlreadyReposted: Пост уже репостнут
            CantRepostYourPost: Нельзя репостить самого себя
            ValidationError: Ошибка валидации

        Returns:
            NewPost: Новый пост
        """
        res = repost(self.token, id, content)

        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Post')
        if res.json().get('error', {}).get('code') == 'CONFLICT':
            raise AlreadyReposted()
        if res.status_code == 422 and res.json().get('message') == 'Cannot repost your own post':
            raise CantRepostYourPost()
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        res.raise_for_status()

        return NewPost.model_validate(res.json())

    @refresh_on_error
    def view_post(self, id: UUID) -> None:
        """Просмотреть пост

        Args:
            id (UUID): UUID поста

        Raises:
            NotFound: Пост не найден
        """
        res = view_post(self.token, id)
        if res.status_code == 204:
            return
        if res.json().get('error', {}).get('code') == 'NOT_FOUND':
            raise NotFound('Post')
        res.raise_for_status()

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
        res = get_liked_posts(self.token, username_or_id, limit, cursor)
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
        res = report(self.token, id, type, reason, description)

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
        res = search(self.token, query, user_limit, hashtag_limit)

        if res.status_code == 414:
            raise TooLarge()
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
    def upload_file(self, name: str, data: BufferedReader) -> File:
        """Загрузить файл

        Args:
            name (str): Имя файла
            data (BufferedReader): Содержимое (open('имя', 'rb'))

        Returns:
            File: Файл
        """
        res = upload_file(self.token, name, data)
        res.raise_for_status()

        return File.model_validate(res.json())

    def update_banner(self, name: str) -> UserProfileUpdate:
        """Обновить банер (шорткат из upload_file + update_profile)

        Args:
            name (str): Имя файла

        Returns:
            UserProfileUpdate: Обновленный профиль
        """
        id = self.upload_file(name, cast(BufferedReader, open(name, 'rb'))).id
        return self.update_profile(banner_id=id)

    @refresh_on_error
    def restore_post(self, post_id: UUID) -> None:
        """Восстановить удалённый пост

        Args:
            post_id: UUID поста
        """
        res = restore_post(self.token, post_id)
        res.raise_for_status()

    @refresh_on_error
    def like_post(self, post_id: UUID) -> int:
        """Лайкнуть пост

        Args:
            post_id (UUID): UUID поста

        Raises:
            NotFound: Пост не найден

        Returns:
            int: Количество лайков
        """
        res = like_post(self.token, post_id)

        if res.status_code == 404:
            raise NotFound("Post")

        return res.json()['likesCount']

    @refresh_on_error
    def unlike_post(self, post_id: UUID) -> int:
        """Убрать лайк с поста

        Args:
            post_id (UUID): UUID поста

        Raises:
            NotFound: Пост не найден

        Returns:
            int: Количество лайков
        """
        res = unlike_post(self.token, post_id)

        if res.status_code == 404:
            raise NotFound("Post not found")

        return res.json()['likesCount']


    @refresh_on_error
    def get_pins(self) -> tuple[list[Pin], str]:
        """Список пинов

        Returns:
            list[Pin]: Список пинов
            str: Активный пин
        """
        res = get_pins(self.token)
        res.raise_for_status()
        data = res.json()['data']

        return [Pin.model_validate(pin) for pin in data['pins']], data['activePin']

    @refresh_on_error
    def remove_pin(self):
        """Снять пин"""
        res = remove_pin(self.token)
        res.raise_for_status()

    @refresh_on_error
    def set_pin(self, slug: str):
        res = set_pin(self.token, slug)
        if res.status_code == 422 and 'found' in res.json():
            raise ValidationError(*list(res.json()['found'].items())[0])
        if res.json().get('error', {}).get('code') == 'PIN_NOT_OWNED':
            raise PinNotOwned(slug)
        res.raise_for_status()

        return res.json()['pin']