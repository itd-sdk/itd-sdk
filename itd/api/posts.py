from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from itd.core.request import endpoint
from itd.enums import PostsTab, UserPostSorting
from itd.exceptions import (
    AlreadyRepostedError,
    BannedWordError,
    CantRepostYourselfError,
    EditExpiredError,
    FeedOverloadedError,
    ForbiddenError,
    NotFoundError,
    NotPinnedError,
    RequiresSubscriptionError,
    TargetUserBannedError,
    ValidationError
)

if TYPE_CHECKING:
    from itd.core.client import Client
    from itd.models.poll import NewPoll


@endpoint(
    'post',
    'posts',
    NotFoundError('Wall recipient'),
    ForbiddenError('post - some files not owned'),
    RequiresSubscriptionError('Video uploading'),
    BannedWordError('Post'),
    ValidationError()
)
def create_post(
    client: Client,
    content: str | None = None,
    spans: list[dict] = [],
    wall_recipient_id: UUID | None = None,
    attachment_ids: list[UUID] = [],
    poll: NewPoll | None = None
):
    data: dict = {'content': content or ''}
    if spans:
        data['spans'] = spans
    if wall_recipient_id:
        data['wallRecipientId'] = str(wall_recipient_id)
    if attachment_ids:
        data['attachmentIds'] = list(map(str, attachment_ids))
    if poll:
        data['poll'] = poll.poll.model_dump(mode='json')

    return data


@endpoint('get', 'posts', ValidationError(), FeedOverloadedError())
def get_posts(client: Client, cursor: str | datetime | None = None, limit: int = 20, tab: PostsTab = PostsTab.POPULAR):
    data: dict = {'limit': limit, 'tab': tab.value}
    if cursor is not None:
        data['cursor'] = cursor
    return data


@endpoint('get', 'posts/{id}', NotFoundError('Post'))
def get_post(client: Client, id: UUID): ...


@endpoint('put', 'posts/{id}', NotFoundError('Post'), ForbiddenError('edit post'), EditExpiredError(), BannedWordError('Post'))
def edit_post(client: Client, id: UUID, content: str, spans: list[dict] = []):
    return {'content': content, 'spans': spans}


@endpoint('delete', 'posts/{id}', NotFoundError('Post'), ForbiddenError('delete post'))
def delete_post(client: Client, id: UUID): ...


@endpoint('post', 'posts/{id}/restore', NotFoundError('Post'), ForbiddenError('restore post'))
def restore_post(client: Client, id: UUID): ...


@endpoint('post', 'posts/{id}/pin', NotFoundError('Post'), ForbiddenError('pin post'))
def pin_post(client: Client, id: UUID): ...


@endpoint('delete', 'posts/{id}/pin', NotPinnedError())
def unpin_post(client: Client, id: UUID): ...


@endpoint('post', 'posts/{id}/repost', NotFoundError('Post'), AlreadyRepostedError(), CantRepostYourselfError(), ValidationError(), BannedWordError('Post'))
def repost(client: Client, id: UUID, content: str | None = None):
    data = {}
    if content:
        data['content'] = content
    return data


@endpoint('get', 'posts/user/{username_or_id}/liked', ValidationError(), NotFoundError('User'))
def get_liked_posts(client: Client, username_or_id: str | UUID, cursor: datetime | None = None, limit: int = 20):
    return {'limit': limit, 'cursor': cursor}


@endpoint(
    'get',
    'posts/user/{username_or_id}',
    ValidationError(),
    NotFoundError('User', res_check=lambda res: res.status_code == 404 and res.text == 'NOT_FOUND'),
    TargetUserBannedError()
)
def get_user_posts(
    client: Client,
    username_or_id: str | UUID,
    cursor: datetime | None = None,
    limit: int = 20,
    pinned_post_id: UUID | None = None,
    sort: UserPostSorting = UserPostSorting.NEW
):
    return {'limit': limit, 'cursor': cursor, 'pinnedPostId': pinned_post_id, 'sort': sort.value}


@endpoint('post', 'posts/{id}/like', NotFoundError('Post'))
def like_post(client: Client, id: UUID): ...


@endpoint('delete', 'posts/{id}/like', NotFoundError('Post'))
def unlike_post(client: Client, id: UUID): ...


@endpoint('post', 'posts/stats', ValidationError())
def get_stats(client: Client, ids: list[UUID]):
    return {'ids': [str(id) for id in ids]}  # if not found, will return empty list
