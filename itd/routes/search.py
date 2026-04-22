from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from itd.client import Client
from itd.exceptions import ValidationError
from itd.base import catch_errors, rate_limit

@rate_limit(None, 0.5, 3)
@catch_errors(ValidationError())
def search(client: Client, query: str, user_limit: int = 5, hashtag_limit: int = 5):
    return client.request('get', 'search', {'userLimit': user_limit, 'hashtagLimit': hashtag_limit, 'q': query})
