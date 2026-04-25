from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

from itd.api.hashtags import get_hashtags, get_posts_by_hashtag
from itd.base import ITDBaseModel, refresh_wrapper
if TYPE_CHECKING:
    from itd.client import Client
    from itd.post import HashtagPosts


class Hashtag(ITDBaseModel):
    _validator = lambda _: _HashtagValidate

    id: UUID
    name: str
    posts_count: int = Field(alias='postsCount')

    def __init__(self, name: str, client: Client | None = None) -> None:
        super().__init__(client)
        self.name = name.lstrip('#')

    @refresh_wrapper
    def refresh(self, client: Client | None = None):
        return get_posts_by_hashtag(client or self.client, self.name, limit=1).json()['data']['hashtag']

    @classmethod
    def _from_dict(cls, data: dict, client: Client | None = None):
        instance = cls(data['name'], client)
        validated = _HashtagValidate.model_validate(data)
        instance._fields_from_data = validated.model_fields_set
        for name, value in validated.__dict__.items():
            setattr(instance, name, value)

        return instance

    def __str__(self) -> str:
        return '#' + self.name

    def __int__(self) -> int:
        return self.posts_count

    @property
    def posts(self) -> 'HashtagPosts':
        if not hasattr(self, '_posts'):
            from itd.post import HashtagPosts
            self._posts = HashtagPosts(self, client=self.client)
        return self._posts



class _HashtagValidate(BaseModel, Hashtag):
    pass