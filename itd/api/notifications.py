from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from itd.core.request import endpoint
from itd.exceptions import NotFoundError

if TYPE_CHECKING:
    from itd.core.client import Client


@endpoint('get', 'notifications')
def get_notifications(client: Client, limit: int = 20, offset: int = 0):
    return {'limit': limit, 'offset': offset}


@endpoint('post', 'notifications/read-batch', NotFoundError('Notification', json_check=lambda json: json.get('success') is False))
def mark_as_read(client: Client, id: UUID):
    return {'ids': [str(id)]}


@endpoint('post', 'notifications/read-all')
def mark_all_as_read(client: Client): ...


@endpoint('get', 'notifications/count')
def get_unread_notifications_count(client: Client): ...


@endpoint('get', 'notifications/settings')
def get_notifications_settings(client: Client): ...


@endpoint('put', 'notifications/settings')
def update_notifications_settings(client: Client, settings: dict):
    return settings


@endpoint('get', 'notifications/stream', sse=True)
def stream_notifications(client: Client): ...
