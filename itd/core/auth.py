from contextlib import contextmanager
from dataclasses import dataclass
from os import getenv
from typing import TYPE_CHECKING

from itd.api.auth import sign_in
from itd.core.captcha import get_turnstile
from itd.core.logger import RICH_AVAILABLE, get_logger, iprint, rich_input
from itd.core.qr import auth_qr
from itd.core.utils import shorten_token
from itd.exceptions import (
    AccessTokenExpiredError,
    CaptchaFailedError,
    EmailDomainNotAllowedError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidEmailError,
    JWTAlgorithmUnsupportedError,
    SessionExpiredError,
    SessionNotFoundError,
    SessionRevokedError
)

if TYPE_CHECKING:
    from itd.core.client import Client

if RICH_AVAILABLE:
    from rich.status import Status

l = get_logger('auth')


@contextmanager
def _status(text: str):
    if not RICH_AVAILABLE:
        iprint(l, text)
        yield None
        return
    with Status(text) as status:
        yield status


def _auth_login(client: 'Client', email: str, password: str) -> bool:
    with _status('Solving captcha..') as status:
        turnstile = get_turnstile(client, status=status)
        if status:
            status.update('Verifying..')
        try:
            apply_auth(client, CredentialsAuth(email, password, turnstile))
        except CaptchaFailedError:
            l.error('captcha verify failed; please fill issue at https://github.com/itd-sdk/itd-sdk/issues/new')
        except InvalidCredentialsError:
            l.error('invalid email or password')
        except EmailDomainNotAllowedError:
            l.error('email domain not allowed')
        except InvalidEmailError:
            l.error('invalid email format')
        else:
            iprint(l, 'accepted')
            return True
    return False


def _auth_refresh(client: 'Client', refresh: str) -> bool:
    with _status('Verifying..'):
        try:
            apply_auth(client, RefreshAuth(refresh))
        except SessionExpiredError:
            l.error('refresh token expired')
        except SessionNotFoundError:
            l.error('invalid refresh token')
        except SessionRevokedError:
            l.error('refresh token revoked')
        else:
            iprint(l, 'accepted')
            return True
    return False


def _auth_access(client: 'Client', access: str) -> bool:
    with _status('Verifying..'):
        try:
            apply_auth(client, AccessAuth(access))
        except AccessTokenExpiredError:
            l.error('access token expired')
        except InvalidAccessTokenError:
            l.error('invalid access token')
        except JWTAlgorithmUnsupportedError:
            l.error('jwt algorithm unsupported')
        else:
            iprint(l, 'accepted')
            return True
    return False


@dataclass
class CredentialsAuth:
    email: str
    password: str
    turnstile: str | None = None


@dataclass
class RefreshAuth:
    refresh: str
    access: str | None = None


@dataclass
class AccessAuth:
    access: str


AuthMethod = CredentialsAuth | RefreshAuth | AccessAuth


def apply_auth(client: 'Client', auth: AuthMethod | None) -> None:
    match auth:
        case CredentialsAuth():
            client._profile.email = auth.email
            client._profile.password = auth.password
            client._profile.creds_valid = True
            client._set_from_profile()
            try:
                res = sign_in(client, auth.email, auth.password, 'turnstileToken', auth.turnstile or get_turnstile(client)[1])
            except Exception:
                client._profile.email = None
                client._profile.password = None
                client._profile.creds_valid = False
                client._set_from_profile()
                raise
            client._profile.set_refresh(res.cookies['refresh_token'], set_expire=True)
            client._profile.set_access(res.json()['accessToken'])

        case RefreshAuth():
            client._profile.set_refresh(auth.refresh, set_expire=True)
            if auth.access:
                client._profile.set_access(auth.access)
            client._set_from_profile()
            try:
                client.refresh_auth()
            except Exception:
                client._profile.refresh_valid = False
                client._set_from_profile()
                raise

        case AccessAuth():
            client._profile.set_access(auth.access)
            client._set_from_profile()
            try:
                client.user.refresh()
            except Exception:
                client._profile.access_valid = False
                client._set_from_profile()
                raise

    client._profile.flush()


def env_auth(client: 'Client') -> bool:
    method = getenv('ITD_AUTH_METHOD')
    if not method:
        return False

    match method:
        case 'login':
            auth = CredentialsAuth(getenv('ITD_LOGIN', ''), getenv('ITD_PASSWORD', ''))
        case 'refresh':
            auth = RefreshAuth(getenv('ITD_REFRESH', ''))
        case 'access':
            auth = AccessAuth(getenv('ITD_ACCESS', ''))
        case 'no':
            auth = None
        case _:
            raise ValueError(f'unknown env auth method {method}')

    apply_auth(client, auth)
    l.info('authorized env method=%s', method)
    return True


def interactive_auth(client: 'Client') -> bool:
    if client._profile._file is None:
        l.debug('create new profile')

    if client._profile.creds_valid or client._profile.refresh_valid or client._profile.access_valid:
        # if not client._profile.access_valid:
        #     client._profile.access = None
        # if not client._profile.refresh_valid:
        #     client._profile.refresh = None
        # if not client._profile.creds_valid:
        #     client._profile.email = None
        #     client._profile.password = None

        return True
    client._credtest = True

    if not client._profile.refresh_valid and client._profile.refresh:
        l.warning('session file refresh token is not valid')

    if not client._profile.creds_valid and client._profile.email:
        l.warning('session file credentials is not valid')

    iprint(
        l, f'session file data: access={shorten_token(client._profile.access)} refresh={shorten_token(client._profile.refresh)} email={client._profile.email}'
    )
    iprint(l, 'select auth option:')
    iprint(l, '[1] Login using credentials')
    iprint(l, '[2] Login via QR code')
    iprint(l, '[3] Manually auth using refresh token')
    iprint(l, '[4] Manually auth using access token')
    iprint(l, '[5] Init client with authorization')
    iprint(l, '[6] Quit')

    while True:
        option = rich_input('option', 'magenta')

        match option:
            case '1':
                if _auth_login(client, rich_input('email', 'green'), rich_input('password', 'green', password=True)):
                    return True
            case '2':
                if auth_qr(client):
                    return True
            case '3':
                if _auth_refresh(client, rich_input('refresh token', 'cyan', password=True)):
                    return True
            case '4':
                l.info('note: authorization will work only for ~15min')
                if _auth_access(client, rich_input('access token', 'cyan')):
                    return True
            case '5':
                return True
            case '6' | 'q' | 'quit':
                quit()
            case _:
                l.error('unknown option')
