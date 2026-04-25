from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID
from os.path import basename
from _io import BufferedReader

from pydantic import BaseModel, Field
from requests import get

from itd.base import ITDBaseModel, refresh_wrapper
from itd.enums import AttachType
from itd.api.files import upload_file, delete_file
if TYPE_CHECKING:
    from itd.client import Client

class File(ITDBaseModel):
    _refreshable = False
    _validator = lambda _: _FileValidate

    id: UUID
    url: str
    filename: str
    mime_type: str = Field(alias='mimeType')
    size: int
    # created_at: datetime | None = Field(None, alias='createdAt')

    def __init__(self, name: str, data: bytes | BufferedReader, client: Client | None = None):
        super().__init__(client)
        self.filename = name
        self._upload(data)

    @classmethod
    def from_path(cls, path: str):
        with open(path, 'rb') as fl:
            return cls(
                basename(path),
                fl
            )

    @classmethod
    def from_bytes(cls, data: bytes | BufferedReader):
        try:
            from filetype import guess
        except ModuleNotFoundError:
            raise ImportError('filetype is required for File.from_bytes. Install by running "uv add itd-sdk[filetype]" (or "pip install itd-sdk[filetype]" if you are using pip)')

        kind = guess(data)
        return cls(
            f'file.{kind.extension}' if kind else 'file.0',
            data
        )

    @refresh_wrapper
    def _upload(self, data: bytes | BufferedReader):
        return upload_file(self.client, self.filename, data).json()

    def delete(self) -> None:
        delete_file(self.client, self.id)

    def download(self, name: str | None = None) -> None:
        with open(name or self.filename, 'wb') as fl:
            fl.write(get(self.url, timeout=60).content)

    def __str__(self) -> str:
        return self.filename


class _FileValidate(BaseModel, File):
    pass



class PostAttach(BaseModel):
    id: UUID
    type: AttachType = AttachType.IMAGE
    url: str
    thumbnail_url: str | None = Field(None, alias='thumbnailUrl')
    width: int | None = None
    height: int | None = None

    def download(self, name: str) -> None:
        with open(name, 'wb') as fl:
            fl.write(get(self.url, timeout=60).content)


class CommentAttach(PostAttach):
    filename: str
    mime_type: str = Field(alias='mimeType')
    size: int
    duration: int | None = None
    order: int = 0

    def download(self, name: str | None = None) -> None:
        with open(name or self.filename, 'wb') as fl:
            fl.write(get(self.url, timeout=60).content)
