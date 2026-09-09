from __future__ import annotations

from typing import TYPE_CHECKING

from itd.core.request import endpoint
from itd.enums import AuthLevel
from itd.exceptions import ValidationError

if TYPE_CHECKING:
    from itd.core.client import Client


@endpoint('get', 'search', ValidationError(), level=AuthLevel.NO)
def search(client: Client, query: str, users_limit: int = 10, hashtags_limit: int = 10):
    return {'userLimit': users_limit, 'hashtagLimit': hashtags_limit, 'q': query}
