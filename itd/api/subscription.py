from __future__ import annotations
from typing import TYPE_CHECKING

from itd.exceptions import NotFound
from itd.base import catch_errors, rate_limit
if TYPE_CHECKING:
    from itd.client import Client

@rate_limit()
@catch_errors()
def get_subscription(client: Client):
    return client.request('get', 'v1/subscription')

@rate_limit()
@catch_errors()
def pay_subscription(client: Client):
    return client.request('post', 'v1/subscription/pay')

@rate_limit()
@catch_errors(NotFound('Subsciption', _subscription_not_found=True))
def toggle_subscription_auto_renewal(client: Client, enabled: bool):
    return client.request('post', 'v1/subscription/auto-renewal', {'enabled': enabled})

@rate_limit()
@catch_errors()
def bind_card(client: Client):
    return client.request('post', 'v1/subscription/bind-card')

@rate_limit()
@catch_errors()
def get_payment_methods(client: Client):
    return client.request('get', 'v1/subscription/methods')

@rate_limit()
@catch_errors()
def set_default_payment_method(client: Client, method: str):
    return client.request('post', f'/v1/subscription/methods/{method}/default')

@rate_limit()
@catch_errors()
def delete_payment_method(client: Client, method: str):
    return client.request('delete', f'/v1/subscription/methods/{method}')