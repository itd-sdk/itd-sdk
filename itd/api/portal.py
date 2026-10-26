from __future__ import annotations

from typing import TYPE_CHECKING

from itd.enums import AuthLevel
from itd.core.request import endpoint

if TYPE_CHECKING:
    from itd.core.client import Client


@endpoint('get', 'v1/portal', level=AuthLevel.NO)
def get_portal(client: Client): ...
