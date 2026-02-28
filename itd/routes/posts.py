from datetime import datetime
from uuid import UUID

from itd.request import fetch
from itd.enums import PostsTab
from itd.models.post import NewPoll

def create_post(token: str, content: str | None = None, spans: list[dict] = [], wall_recipient_id: UUID | None = None, attachment_ids: list[UUID] = [], poll: NewPoll | None = None):
    data: dict = {'content': content or ''}
    if spans:
        data['spans'] = spans
    if wall_recipient_id:
        data['wallRecipientId'] = str(wall_recipient_id)
    if attachment_ids:
        data['attachmentIds'] = list(map(str, attachment_ids))
    if poll:
        data['poll'] = poll.model_dump()

    return fetch(token, 'post', 'posts', data)

def get_posts(token: str, cursor: int = 0, tab: PostsTab = PostsTab.POPULAR):
    return fetch(token, 'get', 'posts', {'cursor': cursor, 'tab': tab.value})

def get_post(token: str, id: UUID):
    return fetch(token, 'get', f'posts/{id}')

def edit_post(token: str, id: UUID, content: str):
    return fetch(token, 'put', f'posts/{id}', {'content': content})

def delete_post(token: str, id: UUID):
    return fetch(token, 'delete', f'posts/{id}')

def pin_post(token: str, id: UUID):
    return fetch(token, 'post', f'posts/{id}/pin')

def repost(token: str, id: UUID, content: str | None = None):
    data = {}
    if content:
        data['content'] = content
    return fetch(token, 'post', f'posts/{id}/repost', data)

def view_post(token: str, id: UUID):
    return fetch(token, 'post', f'posts/{id}/view')

def get_liked_posts(token: str, username_or_id: str | UUID, limit: int = 20, cursor: datetime | None = None):
    return fetch(token, 'get', f'posts/user/{username_or_id}/liked', {'limit': limit, 'cursor': cursor})

def get_user_posts(token: str, username_or_id: str | UUID, limit: int = 20, cursor: datetime | None = None):
    return fetch(token, 'get', f'posts/user/{username_or_id}', {'limit': limit, 'cursor': cursor})

def restore_post(token: str, id: UUID):
    return fetch(token, "post", f"posts/{id}/restore",)

def like_post(token: str, id: UUID):
    return fetch(token, "post", f"posts/{id}/like")

def unlike_post(token: str, id: UUID):
    return fetch(token, "delete", f"posts/{id}/like")

def vote(token: str, id: UUID, options: list[UUID]):
    return fetch(token, 'post', f'posts/{id}/poll/vote', {'optionIds': [str(option) for option in options]})
