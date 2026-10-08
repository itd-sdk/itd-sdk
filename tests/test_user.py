from uuid import UUID, uuid4

import pytest
from helpers import make_client, make_response, make_token

from itd.core.default import set_default_client
from itd.exceptions import PinNotOwnedError
from itd.models.user import Followers, Following, Me, User


@pytest.fixture(scope="module")
def me(client):
    return Me(client)


@pytest.fixture(scope="module")
def me2(client2):
    return Me(client2)


@pytest.fixture
def default_client(keep_default_client):
    """Ленивым тестам нужен только дефолтный клиент: в сеть они не ходят, поэтому TOKEN не нужен"""
    client = make_client(make_token(900))
    set_default_client(client)
    return client


def test_by_username_is_lazy(default_client, fetches):
    user = User.by_username('example')
    assert user.username == 'example'
    assert user._identifier == 'example'
    assert fetches == []


def test_by_id_is_lazy(default_client, fetches):
    uid = UUID('00000000-0000-0000-0000-000000000001')
    user = User.by_id(uid)
    assert user.id == uid
    assert fetches == []


def test_not_loaded_field_still_refreshes(default_client, monkeypatch):
    """Лениво отдаются только те поля, которые задали сами - за остальными модель идет в апи"""
    uid = uuid4()
    calls = []

    def fake_fetch(client, method, url, params={}, files={}, sse=False):
        calls.append(url)
        return make_response(200, {'id': str(uid), 'username': 'example', 'displayName': 'Example'})

    monkeypatch.setattr('itd.core.client.fetch', fake_fetch)

    user = User.by_username('example')
    assert user.display_name == 'Example'
    assert user.id == uid
    assert calls == ['users/example']


def test_me_loads(me):
    assert me.id is not None
    assert me.username
    assert me.display_name


def test_me_to_user_copies_fields(me):
    user = me.to_user()
    assert user.id == me.id
    assert user.username == me.username
    assert user.display_name == me.display_name


def test_me_to_user_is_user_not_me(me):
    user = me.to_user()
    assert isinstance(user, User)
    assert not isinstance(user, Me)


def test_me_followers_instance(me):
    assert isinstance(me.followers, Followers)


def test_me_following_instance(me):
    assert isinstance(me.following, Following)


def test_follow_increments_followers_count(client, me2):
    user = User(me2.username, client)
    is_following = user.is_following
    if is_following:
        user.unfollow(client)

    before = user.followers_count
    assert before is not None
    count = user.follow(client)
    assert count == before + 1

    if not is_following:
        user.unfollow(client)


def test_unfollow_decrements_followers_count(client, me2):
    user = User(me2.username, client)
    is_following = user.is_following
    if not is_following:
        user.follow(client)

    before = user.followers_count
    assert before is not None
    count = user.unfollow(client)
    assert count == before - 1

    if is_following:
        user.follow(client)


def test_block_sets_is_blocking(client, me2):
    user = me2.to_user().for_client(client)
    if user.is_blocking:
        user.unblock(client)
    try:
        user.block(client)
        assert user.is_blocking
    finally:
        user.unblock(client)


def test_unblock_clears_is_blocking(client, me2):
    user = me2.to_user().for_client(client)
    if user.is_blocking:
        user.unblock(client)
    user.block(client)
    user.unblock(client)
    assert not user.is_blocking


def test_set_pin_unknown_slug_raises(me):
    with pytest.raises(PinNotOwnedError):
        me.set_pin('__nonexistent_slug_xyz__')


def test_set_pin_no_pins_raises(me):
    if me.pins:
        pytest.skip('Account has pins')
    with pytest.raises(ValueError, match='No pins available'):
        me.set_pin()


def test_set_pin_updates_user_pin(me):
    if not me.pins:
        pytest.skip('No pins on this account')
    pin = me.pins[0]
    current = me.pin
    pin.set(me.client)
    assert me.pin == pin
    if current:
        current.set(me.client)
    else:
        me.remove_pin()
