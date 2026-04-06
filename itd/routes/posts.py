from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING

from itd.enums import PostsTab, UserPostSorting
from itd.poll import NewPoll
from itd.exceptions import (
    catch_errors, NotFound, Forbidden, RequiresVerification, ValidationError, AlreadyReposted,
    CantRepostYourPost, NotPinned, EditExpired
)

if TYPE_CHECKING:
    from itd.client import Client

@catch_errors(NotFound('Wall recipient'), Forbidden('post - some files not owned'), RequiresVerification('Video uploading'), ValidationError())
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

    return client.request('post', 'posts', data)

@catch_errors(ValidationError())
def get_posts(client: Client, cursor: str | datetime | None = None, limit: int = 20, tab: PostsTab = PostsTab.POPULAR):
    data = {'limit': limit, 'tab': tab.value}
    if cursor is not None:
        data['cursor'] = cursor
    return client.request('get', 'posts', data)

@catch_errors(NotFound('Post'))
def get_post(client: Client, id: UUID):
    return client.request('get', f'posts/{id}')

@catch_errors(NotFound('Post'), Forbidden('edit post'), EditExpired())
def edit_post(client: Client, id: UUID, content: str, spans: list[dict] = []):
    return client.request('put', f'posts/{id}', {'content': content, 'spans': spans})

@catch_errors(NotFound('Post'), Forbidden('delete post'))
def delete_post(client: Client, id: UUID):
    return client.request('delete', f'posts/{id}')

@catch_errors(NotFound('Post'), Forbidden('restore post'))
def restore_post(client: Client, id: UUID):
    return client.request('post', f'posts/{id}/restore')

@catch_errors(NotFound('Post'), Forbidden('pin post'))
def pin_post(client: Client, id: UUID):
    return client.request('post', f'posts/{id}/pin')

@catch_errors(NotPinned())
def unpin_post(client: Client, id: UUID):
    return client.request('delete', f'posts/{id}/pin')

@catch_errors(NotFound('Post'), AlreadyReposted(), CantRepostYourPost(), ValidationError())
def repost(client: Client, id: UUID, content: str | None = None):
    data = {}
    if content:
        data['content'] = content
    return client.request('post', f'posts/{id}/repost', data)

@catch_errors(NotFound('Post'))
def view_post(client: Client, id: UUID):
    return client.request('post', f'posts/{id}/view')

@catch_errors(ValidationError(), NotFound('User'))
def get_liked_posts(client: Client, username_or_id: str | UUID, cursor: datetime | None = None, limit: int = 20):
    return client.request('get', f'posts/user/{username_or_id}/liked', {'limit': limit, 'cursor': cursor})

@catch_errors(ValidationError(), NotFound('User'))
def get_user_posts(client: Client, username_or_id: str | UUID, cursor: datetime | None = None, limit: int = 20, pinned_post_id: UUID | None = None, sort: UserPostSorting = UserPostSorting.NEW):
    return client.request('get', f'posts/user/{username_or_id}', {'limit': limit, 'cursor': cursor, 'pinnedPostId': pinned_post_id, 'sort': sort.value})

@catch_errors(NotFound('Post'))
def like_post(client: Client, id: UUID):
    return client.request('post', f'posts/{id}/like')

@catch_errors(NotFound('Post'))
def unlike_post(client: Client, id: UUID):
    return client.request('delete', f'posts/{id}/like')
