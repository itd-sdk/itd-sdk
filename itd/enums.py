from enum import Enum
from typing import Literal

class RateLimitMode(Enum):
    NO = 'no'
    MIN = 'min' # for one-time actions (eg script just to like post)
    MID = 'mid' # for client apps / basic scripts
    MAX = 'max' # for advanced scripts / userbots

class DebugResponseMode(Enum):
    NO = 'no'
    BEFORE = 'before' # before error checks, raw
    AFTER = 'after' # after error checks, beautitfied
    KEYS = 'keys' # display only keys (after)

class NotificationType(Enum):
    LIKE = 'like'
    COMMENT = 'comment'
    REPLY = 'reply'
    REPOST = 'repost'
    MENTION = 'mention'
    FOLLOW = 'follow'
    FOLLOW_REQUEST = 'follow_request'
    FOLLOW_ACCEPTED = 'follow_accepted'
    COMMENT_LIKE = 'comment_reaction'
    COMMENT_MENTION = 'comment_mention'
    WALL_POST = 'wall_post'

class NotificationTargetType(Enum):
    POST = 'post'

class ReportTargetType(Enum):
    POST = 'post'
    USER = 'user'
    COMMENT = 'comment'

class ReportReason(Enum):
    SPAM = 'spam' # спам
    VIOLENCE = 'violence' # насилие
    HATE = 'hate' # ненависть
    ADULT = 'adult' # 18+
    FRAUD = 'fraud' # обман\мошенничество
    OTHER = 'other' # другое

class AttachType(Enum):
    AUDIO = 'audio'
    IMAGE = 'image'
    VIDEO = 'video'
    FILE = 'file'

class PostsTab(Enum):
    FOLLOWING = 'following'
    POPULAR = 'popular'
    CLAN = 'clan'

class UserPostSorting(Enum):
    POPULAR = 'popular'
    NEW = 'new'

class CommentSorting(Enum): # actually it is not working (stupid itd api)
    POPULAR = 'popular'
    NEW = 'new'
    OLD = 'old'

class AccessType(Enum):
    """Типы разрешений для видимости лайков и записей на стене"""
    NOBODY = 'nobody' # никто
    MUTUAL = 'mutual' # взаимные
    FOLLOWERS = 'followers' # подписчики
    EVERYONE = 'everyone' # все

    def __gt__(self, other):
        return _HIERARCHY.index(self) > _HIERARCHY.index(other)

    def __lt__(self, other):
        return _HIERARCHY.index(self) < _HIERARCHY.index(other)

    def __ge__(self, other):
        return _HIERARCHY.index(self) >= _HIERARCHY.index(other)

    def __le__(self, other):
        return _HIERARCHY.index(self) <= _HIERARCHY.index(other)

_HIERARCHY = [AccessType.EVERYONE, AccessType.FOLLOWERS, AccessType.MUTUAL, AccessType.EVERYONE] # 100% that hierarcy is spelled wrong


class SpanType(Enum):
    MONOSPACE = 'monospace' # моноширный (код)
    STRIKE = 'strike' # зачеркнутый
    BOLD = 'bold' # жирный
    ITALIC = 'italic' # курсив
    SPOILER = 'spoiler' # спойлер
    UNDERLINE = 'underline' # подчеркнутый
    HASHTAG = 'hashtag' # хэштэг (появляется только при получении постов, при создании нету)
    LINK = 'link' # ссылка
    QUOTE = 'quote' # цитата (не работает)
    MENTION = 'mention' # упоминание (появляется только при получении постов, при создании нету)


class Role(Enum):
    USER = 'user'
    ADMIN = 'admin'


class Unset: pass
UNSET = Unset()

class All:
    def __bool__(self) -> Literal[False]:
        return False

ALL = All()
