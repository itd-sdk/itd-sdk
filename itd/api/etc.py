from __future__ import annotations
from typing import TYPE_CHECKING

from itd.base import catch_errors, rate_limit
if TYPE_CHECKING:
    from itd.client import Client

@rate_limit()
@catch_errors()
def get_top_clans(client: Client):
    return client.request('get', 'users/stats/top-clans')

@rate_limit()
@catch_errors()
def get_who_to_follow(client: Client):
    return client.request('get', 'users/suggestions/who-to-follow')
