from __future__ import annotations
from typing import TYPE_CHECKING

from itd.exceptions import PinNotOwned
from itd.base import rate_limit, catch_errors
if TYPE_CHECKING:
    from itd.client import Client

@rate_limit()
@catch_errors()
def get_pins(client: Client):
    return client.request('get', 'users/me/pins')

@rate_limit()
@catch_errors()
def remove_pin(client: Client):
    return client.request('delete', 'users/me/pin')

@rate_limit()
@catch_errors(PinNotOwned())
def set_pin(client: Client, slug: str):
    return client.request('put', 'users/me/pin', {'slug': slug})
