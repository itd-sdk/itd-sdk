from __future__ import annotations
from uuid import UUID
from typing import TYPE_CHECKING

from itd.exceptions import catch_errors, ValidationError, NotFound, AlreadyDeleted

if TYPE_CHECKING:
    from itd.client import Client

@catch_errors(ValidationError(), NotFound('Post'))
def add_comment(client: Client, post_id: UUID, content: str | None = None, attachment_ids: list[UUID] = []):
    return client.request('post', f'posts/{post_id}/comments', {'content': content or '', "attachmentIds": list(map(str, attachment_ids))})

@catch_errors(ValidationError(), NotFound('Comment'), NotFound('User', _reply_comment_user_not_found=True))
def add_reply_comment(client: Client, comment_id: UUID, author_id: UUID, content: str | None = None, attachment_ids: list[UUID] = []):
    return client.request('post', f'comments/{comment_id}/replies', {'content': content or '', 'replyToUserId': str(author_id), "attachmentIds": list(map(str, attachment_ids))})

@catch_errors(ValidationError(), NotFound('Post'))
def get_comments(client: Client, post_id: UUID, cursor: int = 0, limit: int = 20, sort: str = 'popular'):
    return client.request('get', f'posts/{post_id}/comments', {'limit': limit, 'sort': sort, 'cursor': cursor})

@catch_errors(NotFound('Comment'))
def like_comment(client: Client, comment_id: UUID):
    return client.request('post', f'comments/{comment_id}/like')

@catch_errors(NotFound('Comment'))
def unlike_comment(client: Client, comment_id: UUID):
    return client.request('delete', f'comments/{comment_id}/like')

@catch_errors(NotFound('Comment'), AlreadyDeleted('Comment', _delete_comment_not_found=True))
def delete_comment(client: Client, comment_id: UUID):
    return client.request('delete', f'comments/{comment_id}')

@catch_errors(ValidationError(), NotFound('Comment'))
def get_replies(client: Client, comment_id: UUID, page: int = 1, limit: int = 50, sort: str = 'oldest'):
    return client.request('get', f'comments/{comment_id}/replies', {'page': page, 'limit': limit, 'sort': sort})
