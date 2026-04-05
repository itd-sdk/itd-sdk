from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID
from datetime import datetime

from pydantic import Field, BaseModel, field_validator, model_validator

from itd.base import ITDBaseModel
from itd.routes.polls import vote
from itd.utils import parse_datetime
if TYPE_CHECKING:
    from itd.client import Client


class PollOption(ITDBaseModel):
    _refreshable = False

    id: UUID
    text: str
    votes: int = Field(0, alias='votesCount')
    _post_id: UUID

    def __init__(self, data: dict, client: Client | None = None):
        super().__init__(client)

        for name, value in _PollOptionValidate.model_validate(data).__dict__.items():
            setattr(self, name, value)

    def __str__(self) -> str:
        return self.text

    def __int__(self) -> int:
        return self.votes

    def vote(self, client: Client | None = None) -> None:
        vote(client or self.client, self._post_id, [self.id])


class _PollOptionValidate(BaseModel, PollOption):
    pass


class Poll(ITDBaseModel):
    _refreshable = False

    id: UUID
    post_id: UUID = Field(alias='postId')
    created_at: datetime = Field(alias='createdAt')

    question: str
    options: list[PollOption]
    multiple: bool = Field(False, alias='multipleChoice')

    is_voted: bool = Field(False, alias='hasVoted')
    voted_option_ids: list[UUID] = Field([], alias='votedOptionIds')
    total_votes: int = Field(0, alias='totalVotes')

    def __init__(self, poll: dict, client: Client | None = None):
        super().__init__(client)
        for name, value in _PollValidate.model_validate(poll).__dict__.items():
            setattr(self, name, value)

        for option in self.options:
            option._client = self.client

    def __str__(self) -> str:
        return self.question

    def __bool__(self) -> bool:
        return self.is_voted

    def __int__(self) -> int:
        return self.total_votes

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


class _PollValidate(BaseModel, Poll):
    pass

    @field_validator('options', mode='plain')
    @classmethod
    def validate_options(cls, options: list[dict]):
        return [PollOption(option) for option in options]

    @model_validator(mode='after')
    def set_post_id(self) -> '_PollValidate':
        for option in self.options:
            option._post_id = self.post_id
        return self

    @field_validator('created_at', mode='plain')
    @classmethod
    def validate_created_at(cls, created_at: str):
        return parse_datetime(created_at)





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
