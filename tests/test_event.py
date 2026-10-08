"""Действия события: стикеры, шары, окно, шторы, инвентарь - без сети"""

from uuid import uuid4

import pytest
from helpers import make_client, make_response, make_token

from itd.enums import EventItemType
from itd.exceptions import ItemNotFoundError
from itd.models.user import EventProfile, EventSticker, Me

pytestmark = pytest.mark.usefixtures('keep_default_client')

PROFILE_ID = '01a1084a-a98f-729b-bee4-1f9de7e6a16b'
STICKER_ID = '01a111b3-b354-7262-8a36-6af676bdaf2b'

PROFILE = {
    'profileId': PROFILE_ID,
    'rev': 3,
    'window': {'broken': False, 'asset': 'window'},
    'curtains': {'fund': 40, 'goal': 100, 'hasCuratins': False, 'closed': False},
    'placements': [{
        'id': STICKER_ID,
        'kind': 'sticker',
        'asset': 'sticker_1',
        'x': 0.1,
        'y': 0.2,
        'z': 1,
        'size': 1,
        'angle': 0,
        'anchor': {'kind': 'banner'},
        'createdAt': '2026-10-05T12:00:00.000Z',
        'createdBy': str(uuid4())
    }],
    'balloons': []
}

INVENTORY = {
    'items': [
        {'id': str(uuid4()), 'kind': 'sticker', 'asset': 'sticker_2'},
        {'id': str(uuid4()), 'kind': 'eraser'},
        {'id': str(uuid4()), 'kind': 'window', 'asset': 'stone'},
        {'id': str(uuid4()), 'kind': 'stain'}
    ]
}


@pytest.fixture
def api(monkeypatch):
    """Перехватить запросы: отдаем профиль, инвентарь и пустые ответы на действия"""
    calls = []

    def fake_fetch(client, method, url, params={}, files={}, sse=False):
        calls.append({'method': method, 'url': url, 'params': params})
        if url == f'v1/aliceai/profiles/{PROFILE_ID}':
            return make_response(200, PROFILE)
        if url == 'v1/aliceai/inventory':
            return make_response(200, INVENTORY)
        if url.endswith('/window/break'):
            return make_response(200, {'window': {'broken': True, 'asset': 'window_broken', 'brokenAt': '2026-10-08T10:00:00.000Z'}})
        if url.endswith('/placements'):
            return make_response(200, {'placement': dict(PROFILE['placements'][0], id=str(uuid4()), asset='sticker_2')})
        if url.endswith('/balloons'):
            return make_response(200, {'balloon': {
                'id': str(uuid4()), 'x': 0.5, 'y': 0.5, 'angle': 10,
                'thrownAt': '2026-10-08T10:00:00.000Z', 'thrownBy': str(uuid4()),
                'expiresAt': '2026-10-09T10:00:00.000Z', 'anchor': {'kind': 'banner'}
            }})
        return make_response(200, {})

    monkeypatch.setattr('itd.core.client.fetch', fake_fetch)
    return calls


@pytest.fixture
def profile(api):
    client = make_client(make_token(900))
    profile = EventProfile(PROFILE_ID, client=client)
    profile.refresh()
    api.clear()
    return profile


def test_profile_wires_its_parts(profile):
    """Окно, шторы и стикеры должны знать свой профиль - иначе их методы не знают, куда ходить"""
    assert profile.window.profile is profile
    assert profile.curtains.profile is profile
    assert profile.stickers[0].profile is profile


def test_unbound_part_says_what_is_wrong():
    sticker = EventSticker.from_dict(dict(PROFILE['placements'][0]), client=make_client(make_token(900)))

    with pytest.raises(ValueError, match='not bound to a profile'):
        sticker.erase()


def test_break_window_takes_stone_from_inventory(profile, api):
    profile.window.break_window()

    stone = next(item for item in INVENTORY['items'] if item['kind'] == 'window')
    assert api[-1]['url'] == f'v1/aliceai/profiles/{PROFILE_ID}/window/break'
    assert api[-1]['params'] == {'inventoryItemId': stone['id']}
    assert profile.window.broken is True
    assert profile.window.broken_at is not None


def test_break_window_accepts_item_and_id(profile, api):
    stone = next(item for item in profile.client.user.event_inventory if item.type == EventItemType.WINDOW)

    profile.window.break_window(stone)
    assert api[-1]['params'] == {'inventoryItemId': str(stone.id)}

    profile.window.break_window(str(stone.id))
    assert api[-1]['params'] == {'inventoryItemId': str(stone.id)}


def test_place_sticker(profile, api):
    sticker = profile.place_sticker(x=0.3, y=0.7)

    assert api[-1]['url'] == f'v1/aliceai/profiles/{PROFILE_ID}/placements'
    assert api[-1]['params']['x'] == 0.3 and api[-1]['params']['y'] == 0.7
    assert sticker is not None and sticker in profile.stickers
    assert sticker.profile is profile  # у нового стикера тоже должен быть профиль - иначе erase() не сработает


def test_throw_balloon(profile, api):
    balloon = profile.throw_balloon()

    stain = next(item for item in INVENTORY['items'] if item['kind'] == 'stain')
    assert api[-1]['url'] == f'v1/aliceai/profiles/{PROFILE_ID}/balloons'
    assert api[-1]['params']['inventoryItemId'] == stain['id']
    assert balloon is not None and balloon in profile.balloons


def test_erase_sticker_removes_it(profile, api):
    sticker = profile.stickers[0]

    sticker.erase()

    assert api[-1]['url'] == f'v1/aliceai/profiles/{PROFILE_ID}/placements/{STICKER_ID}/erase'
    assert sticker not in profile.stickers


def test_curtains(profile, api):
    assert profile.curtains.donate(70) == 110
    assert api[-1]['params'] == {'amount': 70}
    assert profile.curtains.available is True  # собрали больше goal

    profile.curtains.claim()
    assert api[-1]['url'] == f'v1/aliceai/profiles/{PROFILE_ID}/curtains/claim'

    assert profile.curtains.close() is True
    assert api[-1]['params'] == {'closed': True}
    assert profile.curtains.toggle() is False


def test_take_event_item(api):
    me = Me(client=make_client(make_token(900)))

    assert me.take_event_item(EventItemType.WINDOW).type == EventItemType.WINDOW
    assert len(me.event_items(EventItemType.STICKER)) == 1

    with pytest.raises(ItemNotFoundError, match='No whoopee_cushion item in inventory'):
        me.take_event_item(EventItemType.CUSHION)


def test_inventory_cache_is_dropped_after_action(profile, api):
    me = profile.client.user
    me.event_inventory  # загрузили и закешировали
    assert 'event_inventory' in me.__dict__

    profile.window.break_window()

    assert 'event_inventory' not in me.__dict__, 'камень потрачен, кеш инвентаря надо сбросить'
