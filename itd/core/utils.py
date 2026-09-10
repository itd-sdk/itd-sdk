from datetime import datetime
from sys import version
from uuid import UUID


def get_sdk_user_agent():
    from itd import __version__  # i fucking hate circular imports this is sooo stupid

    return f'itd-sdk/{__version__} (Python/{version})'


def shorten_token(value: str | None, max_len: int = 20):
    if value is None:
        return None

    if len(value) < max_len + 10:
        return value
    return value[: max_len // 2] + '...' + value[-(max_len // 2) :]


def to_uuid(value: str | UUID) -> UUID:
    if isinstance(value, str):
        return UUID(value)
    return value


def to_nullable_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None

    return to_uuid(value)


def parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    v = value.replace('Z', '+00:00')
    try:
        return datetime.strptime(v + '00', '%Y-%m-%d %H:%M:%S.%f%z')
    except ValueError:
        return datetime.fromisoformat(v)
