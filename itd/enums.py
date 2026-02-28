from enum import Enum

class NotificationType(Enum):
    WALL_POST = 'wall_post'
    REPLY = 'reply'
    REPOST = 'repost'
    COMMENT = 'comment'
    FOLLOW = 'follow'
    LIKE = 'like'

class NotificationTargetType(Enum):
    POST = 'post'

class ReportTargetType(Enum):
    POST = 'post'
    USER = 'user'
    COMMENT = 'comment'

class ReportTargetReason(Enum):
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

class AccessType(Enum):
    """Типы разрешений для видимости лайков и записей на стене"""
    NOBODY = 'nobody' # никто
    MUTUAL = 'mutual' # взаимные
    FOLLOWERS = 'followers' # подписчики
    EVERYONE = 'everyone' # все

class SpanType(Enum):
    MONOSPACE = 'monospace' # моноширный (код)
    STRIKE = 'strike' # зачеркнутый
    BOLD = 'bold' # жирный
    ITALIC = 'italic' # курсив
    SPOILER = 'spoiler' # спойлер
    UNDERLINE = 'underline' # подчеркнутый
    HASHTAG = 'hashtag' # хэштэг ? (появляется только при получении постов, при создании нету)
    LINK = 'link' # ссылка
    QUOTE = 'quote' # цитата
