from enum import Enum
from typing import Literal


class AnnouncementButtonStyle(Enum):
    PRIMARY = 'primary'
    SECONDARY = 'secondary'


class AnnouncementButtonType(Enum):
    DISMISS = 'dismiss'
    LINK = 'link'


class InteractionType(Enum):
    PHOTO_OPEN = 1
    VIDEO_PROGRESS = 2


class ViewSource(Enum):
    FEED_GLOBAL = 1
    FEED_FOLLOWING = 2
    FEED_CLAN = 3
    PROFILE = 4
    HASHTAG = 5
    POST_PAGE = 6
    LINK = 7
    SEARCH = 8


class LastSeenUnit(Enum):
    JUST_NOW = 'just_now'
    RECENTLY = 'recently'
    MINUTES = 'minutes'
    HOURS = 'hours'
    THIS_WEEK = 'this_week'
    THIS_MONTH = 'this_month'
    LONG_AGO = 'long_ago'


class ViewReason(Enum):
    NORMAL = 0  # стандартное
    BLUR = 1  # страница скрыта (listener blur)
    HIDDEN = 2  # тоже страница скрыта (listener visibilitychange и доп.проверка что document.hidden)
    PAGE_HIDE = 3  # и это тоже страница скрыта (listener pagehiden)
    UNOBSERVE = 4  # что то заумное на фронтедерском, пост удалили из дома
    INACTIVE = 5  # юзер перестал активить


class AuthLevel(Enum):
    NO = 'no'
    ACCESS = 'access'
    REFRESH = 'refresh'
    LOGIN = 'login'  # todo rename to creds

    def __gt__(self, other):
        return _AUTH_LEVEL_HIERARCHY.index(self) > _AUTH_LEVEL_HIERARCHY.index(other)

    def __lt__(self, other):
        return _AUTH_LEVEL_HIERARCHY.index(self) < _AUTH_LEVEL_HIERARCHY.index(other)

    def __ge__(self, other):
        return _AUTH_LEVEL_HIERARCHY.index(self) >= _AUTH_LEVEL_HIERARCHY.index(other)

    def __le__(self, other):
        return _AUTH_LEVEL_HIERARCHY.index(self) <= _AUTH_LEVEL_HIERARCHY.index(other)


_AUTH_LEVEL_HIERARCHY = [AuthLevel.NO, AuthLevel.ACCESS, AuthLevel.REFRESH, AuthLevel.LOGIN]


class DebugResponseMode(Enum):
    NO = 'no'
    BEFORE = 'before'  # before error checks, raw
    AFTER = 'after'  # after error checks, beautitfied
    KEYS = 'keys'  # display only keys (after)


class UserAgent(Enum):
    BROWSER = 'browser'
    SDK = 'sdk'
    DEFAULT = 'default'
    EMPTY = 'empty'


class NotificationType(Enum):
    LIKE = 'like'
    COMMENT = 'comment'
    REPLY = 'reply'
    REPOST = 'repost'
    MENTION = 'mention'
    FOLLOW = 'follow'
    FOLLOW_REQUEST = 'follow_request'
    FOLLOW_ACCEPTED = 'follow_accepted'
    COMMENT_LIKE = 'comment_like'
    COMMENT_MENTION = 'comment_mention'
    WALL_POST = 'wall_post'


class ParseMode(Enum):
    HTML = 'html'
    MARKDOWN = 'markdown'
    NO = 'no'


class NotificationTargetType(Enum):
    POST = 'post'


class NotificationSubjectType(Enum):
    COMMENT = 'comment'
    POST = 'post'


class ReportTargetType(Enum):
    POST = 'post'
    USER = 'user'
    COMMENT = 'comment'


class ReportReason(Enum):
    SPAM = 'spam'  # спам
    VIOLENCE = 'violence'  # насилие
    HATE = 'hate'  # ненависть
    ADULT = 'adult'  # 18+
    FRAUD = 'fraud'  # обман\мошенничество
    OTHER = 'other'  # другое


class AttachType(Enum):
    AUDIO = 'audio'
    IMAGE = 'image'
    VIDEO = 'video'
    MEDIA = 'media'


class PostsTab(Enum):
    FOLLOWING = 'following'
    POPULAR = 'popular'
    CLAN = 'clan'


class UserPostSorting(Enum):
    POPULAR = 'popular'
    NEW = 'new'


class CommentSorting(Enum):  # actually it is not working (stupid itd api)
    POPULAR = 'popular'
    NEW = 'new'
    OLD = 'old'


class DeviceType(Enum):
    DESKTOP = 'desktop'
    MOBILE = 'mobile'


# class DeviceOS(Enum):
#     WINDOWS = 'Windows'
#     MACOS = 'MacOS'
#     LINUX = 'Linux'
#     ANDROID = 'Android'
#     IOS = 'iOS'


class AccessType(Enum):
    """Типы разрешений для видимости лайков и записей на стене"""

    NOBODY = 'nobody'  # никто
    MUTUAL = 'mutual'  # взаимные
    FOLLOWERS = 'followers'  # подписчики
    EVERYONE = 'everyone'  # все

    def __gt__(self, other):
        return _ACCESS_TYPE_HIERARCHY.index(self) > _ACCESS_TYPE_HIERARCHY.index(other)

    def __lt__(self, other):
        return _ACCESS_TYPE_HIERARCHY.index(self) < _ACCESS_TYPE_HIERARCHY.index(other)

    def __ge__(self, other):
        return _ACCESS_TYPE_HIERARCHY.index(self) >= _ACCESS_TYPE_HIERARCHY.index(other)

    def __le__(self, other):
        return _ACCESS_TYPE_HIERARCHY.index(self) <= _ACCESS_TYPE_HIERARCHY.index(other)


_ACCESS_TYPE_HIERARCHY = [AccessType.EVERYONE, AccessType.FOLLOWERS, AccessType.MUTUAL, AccessType.EVERYONE]  # 100% that hierarcy is spelled wrong


class SpanType(Enum):
    MONOSPACE = 'monospace'  # моноширный (код)
    STRIKE = 'strike'  # зачеркнутый
    BOLD = 'bold'  # жирный
    ITALIC = 'italic'  # курсив
    SPOILER = 'spoiler'  # спойлер
    UNDERLINE = 'underline'  # подчеркнутый
    HASHTAG = 'hashtag'  # хэштэг (появляется только при получении постов, при создании нету)
    LINK = 'link'  # ссылка
    QUOTE = 'quote'  # цитата (не работает)
    MENTION = 'mention'  # упоминание (появляется только при получении постов, при создании нету)


class Role(Enum):
    USER = 'user'
    ADMIN = 'admin'


class LoadStatus(Enum):
    NO = 'no'
    LOADING = 'loading'
    PARTIALLY = 'partially'
    FULL = 'full'


class Unset:
    pass


UNSET = Unset()


class Batch:
    def __bool__(self) -> Literal[False]:
        return False

    def __str__(self) -> str:
        return 'batch'


BATCH = Batch()


class All:
    def __bool__(self) -> Literal[False]:
        return False

    def __str__(self) -> str:
        return 'all'


ALL = All()
