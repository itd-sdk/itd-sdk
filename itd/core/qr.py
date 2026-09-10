from json import loads
from time import sleep
from typing import TYPE_CHECKING, Iterator
from uuid import UUID

from pydantic import BaseModel, Field
from sseclient import SSEClient

from itd.api.auth import qr_claim, qr_start, qr_stream
from itd.core.logger import RICH_AVAILABLE, get_logger, iprint

if TYPE_CHECKING:
    from itd.core.client import Client

try:
    from qrcode import QRCode

    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    from rich.status import Status
except ImportError:
    pass

l = get_logger('qr')


class ITDQRCode(BaseModel):
    id: UUID = Field(alias='qrId')
    payload: str
    claim_token: str = Field(alias='claimToken')
    expires_in: int = Field(90, alias='expiresIn')


class QRLogin:
    def __init__(self, client: 'Client'):
        self.client = client
        self.stream = None
        self.qr = None
        self.refresh()

    def refresh(self) -> ITDQRCode:
        self.close()
        self.qr = ITDQRCode.model_validate(qr_start(self.client).json())
        l.debug('qr code: id=%s claim_token=%s', self.qr.id, self.qr.claim_token)
        return self.qr

    def events(self) -> Iterator[str]:
        assert self.qr
        self.stream = qr_stream(self.client, qr_id=self.qr.id, claim_token=self.qr.claim_token)
        l.debug('start stream')
        try:
            for event in SSEClient(self.stream).events():
                status = loads(event.data)['status']
                l.debug('qr code status: %s', status)
                yield status
                if status in ('approved', 'rejected'):
                    return

        finally:
            self.close()
            l.debug('stop stream')

    def claim(self):
        assert self.qr
        res = qr_claim(self.client, qr_id=self.qr.id, claim_token=self.qr.claim_token)
        self.client._profile.set_refresh(res.cookies['refresh_token'], set_expire=True)
        self.client._profile.set_access(res.json()['accessToken'])

    def close(self):
        if self.stream:
            self.stream.close()
            self.stream = None

    def __enter__(self) -> 'QRLogin':
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def auth_qr(client: 'Client'):
    if not QR_AVAILABLE:
        l.error(r'qrcode library not installed; install via `uv add itd-sdk\[qrcode]`')
        return False

    if RICH_AVAILABLE:
        status = Status('Waiting for scan')
        status.start()
    else:
        status = None

    with QRLogin(client) as qr:
        try:
            for _ in range(5):
                qr.refresh()
                if status:
                    status.update('Generating QR')
                assert qr.qr
                ascii_qr = QRCode(border=2)
                ascii_qr.add_data(qr.qr.payload)
                iprint(l, 'scan QR code with mobile app:')
                ascii_qr.print_ascii(invert=True)
                if status:
                    status.update('Waiting for scan')

                for event in qr.events():
                    if event == 'approved':
                        iprint(l, 'qr code approved')
                        qr.claim()
                        return True

                    elif event == 'rejected':
                        l.error('qr code rejected')
                        break

                    elif event == 'scanned':
                        iprint(l, 'qr code scanned')
                        if status:
                            status.update('Waiting for accept')

                    elif event == 'pending':
                        iprint(l, 'qr code pending')

                    # elif res['status'] == 'captcha_required':
                    #     iprint(l, 'captcha required')
                    #     if status:
                    #         status.update('Solving captcha')
                    #     turnstile = get_turnstile(client)

                sleep(5)

            l.error('all retries to auth qr exceeded')
            return False
        finally:
            if status:
                status.stop()
            if qr.stream:
                qr.stream.close()
