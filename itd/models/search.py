from typing import TYPE_CHECKING

from itd.api.search import search
from itd.core.base import ITDBaseModel
from itd.models.hashtag import Hashtag
from itd.models.user import User

if TYPE_CHECKING:
    from itd.core.client import Client


class Search(ITDBaseModel):
    _refreshable = False
    users: list[User]
    hashtags: list[Hashtag]

    def __init__(self, query: str, users_limit: int = 20, hashtags_limit: int = 20, *, client: 'Client | None' = None):
        super().__init__(client=client)
        self.query = query
        self.users_limit = users_limit
        self.hashtags_limit = hashtags_limit
        self.refresh()

    def refresh(self, client: 'Client | None' = None):
        client = client or self.client
        res = search(client, self.query, self.users_limit, self.hashtags_limit).json()['data']
        self.users = [User.from_dict(user, client=client) for user in res['users']]
        self.hashtags = [Hashtag.from_dict(hashtags, client=client) for hashtags in res['hashtags']]

    def __iter__(self):
        yield from self.users
        yield from self.hashtags

    def __len__(self) -> int:
        return len(self.users) + len(self.hashtags)

    def __bool__(self) -> bool:
        return bool(self.users or self.hashtags)
