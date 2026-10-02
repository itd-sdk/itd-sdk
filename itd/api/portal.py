from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from itd.core.request import endpoint
from itd.enums import AuthLevel

if TYPE_CHECKING:
    from itd.core.client import Client


@endpoint('get', 'v1/portal', level=AuthLevel.NO)
def get_portal(client: Client): ...


@endpoint('get', 'v1/event/status', level=AuthLevel.NO)
def get_event_status(client: Client): ...


@endpoint('get', 'v1/aliceai/profiles/{id}')
def get_event_profile(client: Client, id: UUID): ...


@endpoint('post', 'v1/aliceai/profiles/{id}/claim')
def get_event_profile_fart(client: Client, id: UUID): ...


@endpoint('get', 'event-nicknames')
def get_event_nicknames(client: Client, ids: list[UUID]):
    return {'ids': list(map(str, ids))}


@endpoint('get', 'red-pens/state')
def get_event_posts_red_pens_state(client: Client, ids: list[UUID]):
    return {'ids': list(map(str, ids))}


@endpoint('get', 'correctors/state')
def get_event_posts_correctors_state(client: Client, ids: list[UUID]):
    return {'ids': list(map(str, ids))}


@endpoint('get', 'red-pens/inventory')
def get_event_red_pens_inventory(client: Client): ...


@endpoint('get', 'correctors/inventory')
def get_event_correctors_inventory(client: Client): ...


@endpoint('get', 'v1/aliceai/balance')
def get_event_balance(client: Client): ...


@endpoint('post', 'v1/aliceai/profiles/{id}/curtains/donations')
def donate_event_curtains(client: Client, id: UUID, amount: int):
    return {'amount': amount}
