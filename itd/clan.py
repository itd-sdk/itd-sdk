from pydantic import BaseModel, Field

from itd.base import ITDBaseModel
from itd.api.etc import get_top_clans

class Clan(BaseModel):
    avatar: str
    members_count: int = Field(0, alias='memberCount')


class TopClans(ITDBaseModel, list[Clan]):
    def __init__(self) -> None:
        super().__init__()
        self.refresh()

    def refresh(self):
        self.extend([Clan.model_validate(clan) for clan in get_top_clans(self.client).json()['clans']])