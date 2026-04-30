from __future__ import annotations
from _io import BufferedReader
from uuid import UUID
from typing import TYPE_CHECKING

from itd.base import catch_errors, rate_limit
from itd.exceptions import UploadError, ModerationFailedError, InvalidFileTypeError, TooLargeError
if TYPE_CHECKING:
    from itd.client import Client


@rate_limit(None, None, 1)
@catch_errors(UploadError(), ModerationFailedError(), InvalidFileTypeError(), TooLargeError('File', 413))
def upload_file(client: Client, name: str, data: BufferedReader | bytes):
    return client.request('post', 'files/upload', files={'file': (name, data)})

@rate_limit()
@catch_errors()
def delete_file(client: Client, id: UUID):
    return client.request('delete', f'files/{id}')
