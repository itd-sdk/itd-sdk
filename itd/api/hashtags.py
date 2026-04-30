from __future__ import annotations
from uuid import UUID
from typing import TYPE_CHECKING

from itd.exceptions import TooLargeError, NotFoundError
from itd.base import catch_errors, rate_limit
if TYPE_CHECKING:
    from itd.client import Client

@rate_limit()
@catch_errors()
def get_hashtags(client: Client, limit: int = 10):
    return client.request('get', 'hashtags/trending', {'limit': limit})

@rate_limit()
@catch_errors(TooLargeError('Hashtag'), NotFoundError('Hashtag', _hashtag_not_found=True))
def get_posts_by_hashtag(client: Client, hashtag: str, cursor: UUID | None = None, limit: int = 20):
    return client.request('get', f'hashtags/{hashtag}/posts', {'limit': limit, 'cursor': cursor})
