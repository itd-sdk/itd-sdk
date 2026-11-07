from __future__ import annotations

from codecs import getincrementaldecoder
from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass
class SSEEvent:
    event: str
    data: str


def iter_sse(chunks: Iterable[bytes]) -> Iterator[SSEEvent]:
    """Parse a text/event-stream byte stream into events (WHATWG SSE spec)"""
    decoder = getincrementaldecoder('utf-8')(errors='replace')
    buffer = ''
    event = ''
    data: list[str] = []

    for chunk in chunks:
        buffer += decoder.decode(chunk)
        *lines, buffer = buffer.split('\n')

        for line in lines:
            line = line.removesuffix('\r')
            if not line:
                # blank line dispatches the event
                if data:
                    yield SSEEvent(event, '\n'.join(data))
                event, data = '', []
                continue
            if line.startswith(':'):
                continue  # comment / keep-alive

            field, _, value = line.partition(':')
            value = value.removeprefix(' ')
            if field == 'event':
                event = value
            elif field == 'data':
                data.append(value)
