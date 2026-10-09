from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field

from itd.api.polls import vote
from itd.core.base import ITDBaseModel
from itd.core.utils import parse_datetime

if TYPE_CHECKING:
    from itd.core.client import Client


class PollOption(ITDBaseModel):
    _refreshable = False

    id: UUID
    text: str
    votes: int = Field(0, alias='votesCount')
    position: int
    _post_id: UUID

    def __str__(self) -> str:
        return self.text

    def __int__(self) -> int:
        return self.votes

    def vote(self, client: Client | None = None) -> None:
        vote(client or self.client, self._post_id, [self.id])


class Poll(ITDBaseModel):
    _refreshable = False

    id: UUID
    post_id: UUID = Field(alias='postId')
    created_at: Annotated[datetime, BeforeValidator(parse_datetime)] = Field(alias='createdAt')

    question: str
    options: list[PollOption]
    multiple: bool = Field(False, alias='multipleChoice')

    is_voted: bool = Field(False, alias='hasVoted')
    voted_option_ids: list[UUID] = Field([], alias='votedOptionIds')
    total_votes: int = Field(0, alias='totalVotes')

    def __str__(self) -> str:
        return self.question

    def __bool__(self) -> bool:
        return self.is_voted

    def __int__(self) -> int:
        return self.total_votes

    def _post_refresh(self, context: dict = {}):
        for option in self.options:
            option._post_id = self.post_id

    def vote(self, options: list[str | UUID | PollOption] | str | UUID | PollOption, client: Client | None = None) -> None:
        uuid_options = []
        if isinstance(options, list):
            for option in options:
                if isinstance(option, str):
                    found = [_option for _option in self.options if _option.text == option]
                    if found:
                        uuid_options.append(found[0].id)
                    else:
                        raise ValueError(f'Option "{option}" not found')
                elif isinstance(option, PollOption):
                    uuid_options.append(option.id)
                elif isinstance(option, UUID):
                    uuid_options.append(option)
                else:
                    raise TypeError(f'Invalid option type (should be str, PollOption or UUID), got "{type(option)}"')
        else:
            option = options
            if isinstance(option, str):
                found = [_option for _option in self.options if _option.text == option]
                if found:
                    uuid_options.append(found[0].id)
                else:
                    raise ValueError(f'Option "{option}" not found')
            elif isinstance(option, PollOption):
                uuid_options.append(option.id)
            elif isinstance(option, UUID):
                uuid_options.append(option)
            else:
                raise TypeError(f'Invalid option type (should be str, PollOption or UUID), got "{type(option)}"')

        vote(client or self.client, self.post_id, uuid_options)


class _NewPollOption(BaseModel):
    text: str


class _NewPoll(BaseModel):
    multiple: bool = Field(False, alias='multipleChoice')
    question: str
    options: list[_NewPollOption]

    model_config = {'serialize_by_alias': True}


class NewPoll:
    def __init__(self, question: str, options: list[str], multiple: bool = False):
        self.poll = _NewPoll(question=question, options=[_NewPollOption(text=option) for option in options], multipleChoice=multiple)

    @classmethod
    def from_poll(cls, poll: Poll):
        return cls(poll.question, list(map(str, poll.options)), poll.multiple)
