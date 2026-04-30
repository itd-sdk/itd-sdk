from __future__ import annotations
from uuid import UUID
from typing import TYPE_CHECKING

from itd.base import catch_errors, rate_limit
from itd.exceptions import ValidationError, NotFoundError, AlreadyDeletedError, BannedWordError

if TYPE_CHECKING:
    from itd.client import Client

@rate_limit(5, 20, 80)
@catch_errors(ValidationError(), NotFoundError('Post'), BannedWordError('Comment'))
def add_comment(client: Client, post_id: UUID, content: str | None = None, attachment_ids: list[UUID] = []):
    return client.request('post', f'posts/{post_id}/comments', {'content': content or '', "attachmentIds": list(map(str, attachment_ids))})

@rate_limit(1, 10, 30)
@catch_errors(ValidationError(), NotFoundError('Comment'), NotFoundError('User', _reply_comment_user_not_found=True), BannedWordError('Reply'))
def add_reply_comment(client: Client, comment_id: UUID, author_id: UUID, content: str | None = None, attachment_ids: list[UUID] = []):
    return client.request('post', f'comments/{comment_id}/replies', {'content': content or '', 'replyToUserId': str(author_id), "attachmentIds": list(map(str, attachment_ids))})

@rate_limit()
@catch_errors(ValidationError(), NotFoundError('Post'))
def get_comments(client: Client, post_id: UUID, cursor: int = 0, limit: int = 20, sort: str = 'popular'):
    return client.request('get', f'posts/{post_id}/comments', {'limit': limit, 'sort': sort, 'cursor': cursor})

@rate_limit(None, 3, 15)
@catch_errors(NotFoundError('Comment'))
def like_comment(client: Client, comment_id: UUID):
    return client.request('post', f'comments/{comment_id}/like')

@rate_limit()
@catch_errors(NotFoundError('Comment'))
def unlike_comment(client: Client, comment_id: UUID):
    return client.request('delete', f'comments/{comment_id}/like')

@rate_limit()
@catch_errors(NotFoundError('Comment'), AlreadyDeletedError('Comment', _delete_comment_not_found=True))
def delete_comment(client: Client, comment_id: UUID):
    return client.request('delete', f'comments/{comment_id}')

@rate_limit()
@catch_errors(ValidationError(), NotFoundError('Comment'))
def get_replies(client: Client, comment_id: UUID, page: int = 1, limit: int = 50, sort: str = 'oldest'):
    return client.request('get', f'comments/{comment_id}/replies', {'page': page, 'limit': limit, 'sort': sort})
