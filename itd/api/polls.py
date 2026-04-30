from __future__ import annotations
# moved from posts.py due to circular import
from uuid import UUID
from typing import TYPE_CHECKING

from itd.exceptions import NotFoundError, OptionsNotBelongError, NotMultipleChoiceError
from itd.base import catch_errors, rate_limit

if TYPE_CHECKING:
    from itd.client import Client


@rate_limit()
@catch_errors(NotFoundError('Post'), NotFoundError('Poll', 'Опрос не найден'), OptionsNotBelongError(), NotMultipleChoiceError())
def vote(client: Client, id: UUID, options: list[UUID]):
    return client.request('post', f'posts/{id}/poll/vote', {'optionIds': [str(option) for option in options]})
