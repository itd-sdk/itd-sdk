from uuid import UUID
from datetime import datetime

from pydantic import Field, BaseModel, field_validator

from itd.models.user import UserPost, UserNewPost
from itd.models._text import TextObject
from itd.models.file import PostAttach
from itd.models.comment import Comment
from itd.enums import SpanType


class NewPollOption(BaseModel):
    text: str


class PollOption(NewPollOption):
    id: UUID
    position: int = 0
    votes: int = Field(0, alias='votesCount')


class _Poll(BaseModel):
    multiple: bool = Field(False, alias='multipleChoice')
    question: str


class NewPoll(_Poll):
    options: list[NewPollOption]
    model_config = {'serialize_by_alias': True}


class PollData:
    def __init__(self, question: str, options: list[str], multiple: bool = False):
        self.poll = NewPoll(question=question, options=[NewPollOption(text=option) for option in options], multipleChoice=multiple)


class Poll(_Poll):
    id: UUID
    post_id: UUID = Field(alias='postId')

    options: list[PollOption]
    votes: int = Field(0, alias='totalVotes')
    is_voted: bool = Field(False, alias='hasVoted')
    voted_option_ids: list[UUID] = Field([], alias='votedOptionIds')

    created_at: datetime = Field(alias='createdAt')

    @field_validator('created_at', mode='plain')
    @classmethod
    def validate_created_at(cls, v: str):
        v = v.replace('Z', '+00:00')
        try:
            return datetime.strptime(v + '00', '%Y-%m-%d %H:%M:%S.%f%z')
        except ValueError:
            return datetime.fromisoformat(v)


class Span(BaseModel):
    length: int
    offset: int
    type: SpanType
    url: str | None = None


class _PostCounts(TextObject):
    likes_count: int = Field(0, alias='likesCount')
    comments_count: int = Field(0, alias='commentsCount')
    reposts_count: int = Field(0, alias='repostsCount')
    views_count: int = Field(0, alias='viewsCount')

    spans: list[Span] = []


class _PostAuthor(_PostCounts):
    author: UserPost


class OriginalPost(_PostAuthor):
    is_deleted: bool = Field(False, alias='isDeleted')


class Post(_PostCounts, _PostAuthor):
    poll: Poll | None = None
    dominant: str | None = Field(None, alias='dominantEmoji')
    edited_at: datetime | None = Field(None, alias='editedAt')

    is_liked: bool = Field(False, alias='isLiked')
    is_reposted: bool = Field(False, alias='isReposted')
    is_viewed: bool = Field(False, alias='isViewed')
    is_owner: bool = Field(False, alias='isOwner')
    is_pinned: bool = Field(False, alias='isPinned')  # only for user wall

    attachments: list[PostAttach] = []
    comments: list[Comment] = []

    original_post: OriginalPost | None = None  # for reposts

    wall_recipient_id: UUID | None = Field(None, alias='wallRecipientId')
    wall_recipient: UserPost | None = Field(None, alias='wallRecipient')

    @field_validator('edited_at', mode='plain')
    @classmethod
    def validate_edited_at(cls, v: str | None):
        if v is None:
            return
        v = v.replace('Z', '+00:00')
        try:
            return datetime.strptime(v + '00', '%Y-%m-%d %H:%M:%S.%f%z')
        except ValueError:
            return datetime.fromisoformat(v)
