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
    from itd.core.config import Config

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
    def __init__(self):
        from itd import init_not_authed_client

        self.client = init_not_authed_client()
        self.stream = None
        self.qr = None
        self.auth = None
        self.status = 'pending'
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
                self.status = loads(event.data)['status']
                l.debug('qr code status: %s', self.status)
                yield self.status
                if self.status in ('approved', 'rejected'):
                    break

            if self.status == 'approved':
                self.claim()
                self.status = 'authorized'
                yield 'authorized'
            elif self.status != 'rejected':
                l.debug('expire qr')
                self.status = 'expired'
                yield 'expired'

        finally:
            self.close()
            l.debug('stop stream')

    def claim(self):
        from itd.core.auth import RefreshAuth

        assert self.qr
        res = qr_claim(self.client, qr_id=self.qr.id, claim_token=self.qr.claim_token)
        self.auth = RefreshAuth(res.cookies['refresh_token'], res.json()['accessToken'])

    def get_client(self, name: str | None = None, config: 'Config | None' = None):
        from itd import ITDConfig, init_client

        if config is None:
            config = ITDConfig()
        config.is_default = True

        assert self.auth
        return init_client(name, config, auth=self.auth)

    def close(self):
        if self.stream:
            self.stream.close()
            self.stream = None

    def __enter__(self) -> 'QRLogin':
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def interactive_auth_qr(client: 'Client'):
    if not QR_AVAILABLE:
        l.error(r'qrcode library not installed; install via `uv add itd-sdk\[qrcode]`')
        return False

    if RICH_AVAILABLE:
        status = Status('Waiting for scan')
        status.start()
    else:
        status = None

    with QRLogin() as qr:
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
                        assert qr.auth
                        assert qr.auth.access
                        client._profile.set_access(qr.auth.access)
                        client._profile.set_refresh(qr.auth.refresh, set_expire=True)
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
