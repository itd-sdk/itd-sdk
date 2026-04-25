from __future__ import annotations
from typing import TYPE_CHECKING

from itd.base import catch_errors, rate_limit
if TYPE_CHECKING:
    from itd.client import Client

@rate_limit()
@catch_errors()
def verify(client: Client, file_url: str):
    # {"success":true,"request":{"id":"fc54e54f-8586-4d8c-809e-df93161f99da","userId":"9096a85b-c319-483e-8940-6921be427ad0","videoUrl":"https://943701f000610900cbe86b72234e451d.bckt.ru/videos/354f28a6-9ac7-48a6-879a-a454062b1d6b.mp4","status":"pending","rejectionReason":null,"reviewedBy":null,"reviewedAt":null,"createdAt":"2026-01-30T12:58:14.228Z","updatedAt":"2026-01-30T12:58:14.228Z"}}
    return client.request('post', 'verification/submit', {'videoUrl': file_url})

@rate_limit()
@catch_errors()
def get_verification_status(client: Client):
    return client.request('get', 'verification/status')
