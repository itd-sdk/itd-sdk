from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic import BaseModel

from itd.base import ITDBaseModel
from itd.api.pins import set_pin, remove_pin

if TYPE_CHECKING:
    from itd.client import Client
    from itd.user import _UserBase


class Pin(ITDBaseModel):
    _refreshable = False
    _validator = lambda _: _PinValidate
    _user: '_UserBase'

    slug: str
    name: str
    description: str

    def __init__(self, pin: dict, user: '_UserBase | None' = None, client: Client | None = None):
        super().__init__(client)

        for name, value in _PinValidate.model_validate(pin).__dict__.items():
            setattr(self, name, value)

        if user:
            self._user = user

    def __str__(self) -> str:
        return self.name

    def set(self, client: Client | None = None) -> None:
        set_pin(client or self.client, self.slug)
        self._user.pin = self

    def remove(self, client: Client | None = None) -> None:
        remove_pin(client or self.client)
        self._user.pin = None


class _PinValidate(BaseModel, Pin):
    pass