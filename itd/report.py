from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from itd.base import ITDBaseModel, refresh_wrapper
from itd.enums import ReportReason, ReportTargetType
from itd.api.reports import report
if TYPE_CHECKING:
    from itd.client import Client

class Report(ITDBaseModel):
    _refreshable = False
    _validator = lambda _: _ReportValidate

    id: UUID
    created_at: datetime = Field(alias='createdAt')

    def __init__(self, target_id: UUID, target_type: ReportTargetType, reason: ReportReason, description: str | None = None, client: Client | None = None):
        super().__init__(client)

        self.target_id = target_id
        self.target_type = target_type
        self.reason = reason
        self.description = description

        self.refresh()


    @refresh_wrapper
    def refresh(self, client: Client | None = None):
        return report(client or self.client, self.target_id, self.target_type, self.reason, self.description).json()['data']



class _ReportValidate(BaseModel, Report):
    pass