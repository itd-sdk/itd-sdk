from datetime import datetime

import pytest

from itd.user import Me


@pytest.fixture(scope="module")
def me_sub(client_sub):
    return Me(client_sub)


@pytest.fixture(scope="module")
def sub(me_sub):
    return me_sub.subscription


def test_subscription_is_active(sub):
    assert sub.active


def test_subscription_expires_in_future(sub):
    assert sub.expires_at is not None
    assert sub.expires_at > datetime.now(sub.expires_at.tzinfo)


def test_subscription_bool(sub):
    assert bool(sub)


def test_auto_renewal_is_bool(sub):
    assert isinstance(sub.auto_renewal, bool)


def test_set_auto_renewal(sub):
    original = sub.auto_renewal
    result = sub.set_auto_renewal(not original)
    assert result == (not original)
    assert sub.auto_renewal == (not original)
    sub.set_auto_renewal(original)


def test_toggle_auto_renewal(sub):
    original = sub.auto_renewal
    toggled = sub.toggle_auto_renewal()
    assert toggled == (not original)
    sub.set_auto_renewal(original)


def test_payment_methods_is_list(sub):
    assert isinstance(sub.payment_methods, list)


def test_pay_returns_url(me_sub):
    url = me_sub.subscription.pay()
    assert isinstance(url, str)
    assert url.startswith('http')
