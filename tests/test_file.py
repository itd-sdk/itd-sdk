from pathlib import Path
from uuid import UUID

import pytest

from itd.file import File


MP3_PATH = Path(__file__).parent.parent / '1.mp3'


@pytest.fixture(scope="module")
def mp3_bytes():
    return MP3_PATH.read_bytes()


@pytest.fixture
def uploaded(client, mp3_bytes):
    f = File('1.mp3', mp3_bytes, client)
    yield f
    try:
        f.delete()
    except Exception:
        pass


def test_upload_from_bytes(uploaded, mp3_bytes):
    assert isinstance(uploaded.id, UUID)
    assert uploaded.filename == '1.mp3'
    assert uploaded.url.startswith('http')
    assert uploaded.size == len(mp3_bytes)


def test_upload_from_path(client):
    f = File.from_path(str(MP3_PATH))
    assert isinstance(f.id, UUID)
    assert f.filename == '1.mp3'
    f.delete()


def test_file_str(uploaded):
    assert str(uploaded) == uploaded.filename


def test_file_delete(client, mp3_bytes):
    f = File('to_delete.mp3', mp3_bytes, client)
    f.delete()


def test_file_download(uploaded, tmp_path, mp3_bytes):
    out = tmp_path / 'downloaded.mp3'
    uploaded.download(str(out))
    assert out.exists()
    assert out.read_bytes() == mp3_bytes
