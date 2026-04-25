import pytest

from itd.user import Me
from itd.enums import AccessType


@pytest.fixture(scope="module")
def me(client):
    return Me(client)


# --- Profile ---

def test_profile_loads(me):
    assert me.profile is not None


def test_profile_authenticated(me):
    assert me.profile.authenticated


def test_profile_user_matches_me(me):
    assert me.profile.user is not None
    assert me.profile.user.id == me.id
    assert me.profile.user.username == me.username


def test_profile_not_banned(me):
    assert not me.profile.banned


def test_profile_user_has_roles(me):
    assert len(me.profile.user.roles) > 0


# --- Privacy ---

def test_privacy_loads(me):
    assert me.privacy is not None


def test_privacy_wall_access_is_access_type(me):
    assert isinstance(me.privacy.wall_access, AccessType)


def test_privacy_likes_visibility_is_access_type(me):
    assert isinstance(me.privacy.likes_visibility, AccessType)


def test_privacy_show_last_seen_is_bool(me):
    assert isinstance(me.privacy.show_last_seen, bool)


def test_privacy_is_private_is_bool(me):
    assert isinstance(me.privacy.is_private, bool)


def test_privacy_syncs_with_me(me):
    assert me.privacy.is_private == me.is_private
    assert me.privacy.wall_access == me.wall_access
    assert me.privacy.likes_visibility == me.likes_visibility


def test_privacy_update_show_last_seen(me):
    original = me.privacy.show_last_seen
    me.privacy.update(show_last_seen=not original)
    assert me.privacy.show_last_seen == (not original)
    me.privacy.update(show_last_seen=original)


def test_privacy_update_from_fields(me):
    original = me.privacy.show_last_seen
    me.privacy.show_last_seen = not original
    me.privacy.update_from_fields()
    assert me.privacy.show_last_seen == (not original)
    me.privacy.update(show_last_seen=original)
