from __future__ import annotations
from typing import TYPE_CHECKING

from requests import Response

from itd.base import catch_errors
from itd.request import fetch
from itd.exceptions import InvalidPasswordError, SamePasswordError, InvalidOldPasswordError, SessionNotFoundError, SessionExpiredError
if TYPE_CHECKING:
    from itd.client import Client

@catch_errors(SessionExpiredError(), SessionNotFoundError())
def refresh_token(client: Client) -> Response:
    return fetch(client, 'post', 'v1/auth/refresh')

@catch_errors(InvalidPasswordError(), SamePasswordError(), InvalidOldPasswordError())
def change_password(client: Client, old: str, new: str) -> Response:
    return client.request('post', 'v1/auth/change-password', {'newPassword': new, 'oldPassword': old})

@catch_errors()
def logout(client: Client) -> Response:
    return client.request('post', 'v1/auth/logout')
