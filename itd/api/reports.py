from __future__ import annotations
from uuid import UUID
from typing import TYPE_CHECKING

from itd.enums import ReportReason, ReportTargetType
from itd.exceptions import AlreadyReported, NotFound, ValidationError
from itd.base import catch_errors, rate_limit

if TYPE_CHECKING:
    from itd.client import Client

@rate_limit(5, 30, 60) # это стоило мне одного ака виталия
@catch_errors(AlreadyReported(), NotFound('Report target', _report_target_not_found=True), ValidationError())
def report(client: Client, id: UUID, type: ReportTargetType = ReportTargetType.POST, reason: ReportReason = ReportReason.OTHER, description: str | None = None):
    if description is None:
        description = ''
    return client.request('post', 'reports', {'targetId': str(id), 'targetType': type.value, 'reason': reason.value, 'description': description})
