from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from itd.core.request import endpoint
from itd.enums import AuthLevel
from itd.exceptions import ItemNotFoundError

if TYPE_CHECKING:
    from itd.core.client import Client


@endpoint('get', 'v1/portal', level=AuthLevel.NO)
def get_portal(client: Client): ...


@endpoint('get', 'v1/event/status', level=AuthLevel.NO)
def get_event_status(client: Client): ...


@endpoint('get', 'v1/aliceai/profiles/{id}')
def get_event_profile(client: Client, id: UUID): ...


@endpoint('post', 'v1/aliceai/profiles/{id}/claim')
def event_profile_claim_fart(client: Client, id: UUID): ...


@endpoint('post', 'v1/aliceai/profiles/{id}/cushion', ItemNotFoundError())
def event_profile_put_fart(client: Client, id: UUID, item_id: UUID, x: float, y: float):
    return {'inventoryItemId': str(item_id), 'anchorKind': 'profile_header', 'anchorId': None, 'x': x, 'y': y}


@endpoint('get', 'event-nicknames')
def get_event_nicknames(client: Client, ids: list[UUID]):
    return {'ids': ','.join(map(str, ids))}


@endpoint('get', 'red-pens/state')
def get_event_posts_red_pens_state(client: Client, ids: list[UUID]):
    return {'ids': ','.join(map(str, ids))}


@endpoint('get', 'correctors/state')
def get_event_posts_correctors_state(client: Client, ids: list[UUID]):
    return {'ids': ','.join(map(str, ids))}


@endpoint('get', 'red-pens/inventory')
def get_event_red_pens_inventory(client: Client): ...


@endpoint('get', 'correctors/inventory')
def get_event_correctors_inventory(client: Client): ...


@endpoint('get', 'v1/aliceai/balance')
def get_event_balance(client: Client): ...


@endpoint('post', 'v1/aliceai/profiles/{id}/curtains/donations')
def donate_event_curtains(client: Client, id: UUID, amount: int):
    return {'amount': amount}


@endpoint('post', 'v1/aliceai/profiles/{id}/curtains/claim')
def claim_event_curtains(client: Client, id: UUID): ...


@endpoint('put', 'v1/aliceai/profiles/{id}/curtains')
def set_event_curtains(client: Client, id: UUID, state: bool):
    return {'closed': state}


@endpoint('post', 'v1/aliceai/waste-paper/posts/{id}')
def event_recycle_post(client: Client, id: UUID): ...


@endpoint('get', 'v1/aliceai/inventory')
def get_my_event_inventory(client: Client): ...


@endpoint('get', 'v1/aliceai/nicknames')
def get_my_event_nicknames(client: Client): ...


@endpoint('put', 'v1/aliceai/nicknames/active')
def set_event_nickname(client: Client, nickname_id: str | None):
    return {'form': nickname_id}


@endpoint('get', 'profile-avatar')
def get_profile_avatar(client: Client): ...


@endpoint('delete', 'profile-avatar')
def delete_profile_avatar(client: Client): ...


@endpoint('post', 'v1/aliceai/profiles/{id}/placements', ItemNotFoundError())
def place_event_sticker(client: Client, id: UUID, item_id: UUID, x: float, y: float, anchor: dict | None = None):
    data: dict = {'inventoryItemId': str(item_id), 'x': x, 'y': y}
    if anchor:
        data['anchor'] = anchor
    return data


@endpoint('post', 'v1/aliceai/profiles/{id}/balloons', ItemNotFoundError())
def place_event_balloons(client: Client, id: UUID, item_id: UUID, x: float, y: float, anchor: dict | None = None):
    data: dict = {'inventoryItemId': str(item_id), 'x': x, 'y': y}
    if anchor:
        data['anchor'] = anchor
    return data


@endpoint('post', 'v1/aliceai/profiles/{id}/window/break', ItemNotFoundError())
def break_event_window(client: Client, id: UUID, item_id: UUID):
    return {'inventoryItemId': str(item_id)}


@endpoint('post', 'v1/aliceai/profiles/{id}/placements/{sticker_id}/erase', ItemNotFoundError())
def erase_event_sticker(client: Client, id: UUID, sticker_id: UUID): ...


# operationId - ключ идемпотентности: сайт генерирует новый на каждое применение
@endpoint('post', 'red-pens/apply')
def apply_red_pen(client: Client, id: UUID, event_id: str, revision: str, start: int, end: int, replacement: str, operation_id: UUID | str | None = None):
    return {
        'postId': str(id),
        'eventId': event_id,
        'revision': revision,
        'start': start,
        'end': end,
        'replacement': replacement,
        'operationId': str(operation_id or uuid4()),
    }


@endpoint('post', 'correctors/apply')
def apply_corrector(client: Client, id: UUID, event_id: str, revision: str, start: int, end: int, operation_id: UUID | str | None = None):
    return {'postId': str(id), 'eventId': event_id, 'revision': revision, 'start': start, 'end': end, 'operationId': str(operation_id or uuid4())}


@endpoint('post', 'correctors/cancel')
def cancel_corrector(client: Client, id: UUID):
    return {'postId': str(id)}


@endpoint('post', 'red-pens/cancel')
def cancel_red_pen(client: Client, id: UUID, claim_id: str):
    return {'postId': str(id), 'claimId': str(claim_id)}


@endpoint('post', 'correctors/report')
def report_corrector(client: Client, id: UUID, mark_id: UUID, reason: str = 'Неприемлемая правка'):
    return {'postId': str(id), 'markId': str(mark_id), 'reason': reason}


@endpoint('post', 'red-pens/report')
def report_red_pen(client: Client, id: UUID, claim_id: UUID, reason: str = 'Неприемлемая правка'):
    return {'postId': str(id), 'claimId': str(claim_id), 'reason': reason}
