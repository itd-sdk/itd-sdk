from __future__ import annotations
from uuid import UUID
from typing import TYPE_CHECKING

from itd.request import fetch_stream
from itd.base import catch_errors, rate_limit

if TYPE_CHECKING:
    from itd.client import Client

@rate_limit()
@catch_errors()
def get_notifications(client: Client, limit: int = 20, offset: int = 0):
    return client.request('get', 'notifications', {'limit': limit, 'offset': offset})

@rate_limit()
@catch_errors()
def mark_as_read(client: Client, id: UUID):
    return client.request('post', f'notifications/{id}/read')

@rate_limit()
@catch_errors()
def mark_all_as_read(client: Client):
    return client.request('post', 'notifications/read-all')

@rate_limit()
@catch_errors()
def get_unread_notifications_count(client: Client):
    return client.request('get', 'notifications/count')


def stream_notifications(client: Client):
    """Получить SSE поток уведомлений

    Returns:
        Response: Streaming response для SSE
    """
    return fetch_stream(client.token, 'notifications/stream', session=client.session)
