from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from json import dumps
from uuid import uuid4

from itd.core.sse import SSEEvent, iter_sse
from itd.enums import NotificationType
from itd.models.notification import Notifications

from itd.core.client import Config


def test_iter_sse_spec():
    raw = b'event:a\r\ndata: {"x":\r\ndata:1}\r\n\r\n: keep-alive\n\ndata: no-event\n\n'
    # split into tiny chunks to cover buffering and multibyte decoding
    chunks = [raw[i : i + 3] for i in range(0, len(raw), 3)]
    assert list(iter_sse(chunks)) == [SSEEvent('a', '{"x":\n1}'), SSEEvent('', 'no-event')]


def test_iter_sse_utf8_split():
    raw = 'data: привет\n\n'.encode()
    assert list(iter_sse(raw[i : i + 1] for i in range(len(raw)))) == [SSEEvent('', 'привет')]


class FakeStream:
    def __init__(self, data: bytes):
        self.data = data

    def iter_content(self, chunk_size=None):
        yield self.data

    def close(self): ...


def sse(event: str, data: dict) -> str:
    return f'event: {event}\ndata: {dumps(data)}\n\n'


def make_ntf(type: str, **extra) -> dict:
    return {'id': str(uuid4()), 'type': type, 'createdAt': datetime.now(timezone.utc).isoformat(), **extra}


def test_stream_dispatch(monkeypatch):
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    reminder = make_ntf('alice_task_reminder', title='t', eventId='e1', expiresAt=future)
    body = (
        sse('connected', {'userId': 'u', 'timestamp': 1})
        + sse('notification', make_ntf('follow'))
        + sse('notification.event', reminder)
        + sse('notification.event', reminder)  # duplicate
        + sse('notification.event', make_ntf('alice_task_reminder', eventId='e2', expiresAt=past))
        + sse('alice.bell', {'id': 'b', 'expiresAt': future})
        + sse('notification.event-ended', {'eventId': 'e1'})
    )
    monkeypatch.setattr('itd.models.notification.stream_notifications', lambda client: FakeStream(body.encode()))

    ntfs = Notifications(SimpleNamespace(config=Config()))  # type: ignore
    ntfs._unread = 0
    got, ended = [], []
    ntfs.on_alice_task_reminder = got.append
    ntfs.on_event_ended = ended.append

    types = [n.type for n in ntfs.stream()]
    assert types == [NotificationType.FOLLOW, NotificationType.EVENT_REMINDER]
    assert got[0].event_id == 'e1'
    assert ended == ['e1']
    assert [n.type for n in list.__iter__(ntfs)] == [NotificationType.FOLLOW]
    assert ntfs._unread == 1
