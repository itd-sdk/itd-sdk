from datetime import datetime
from typing import Callable, cast

from requests import Response

from itd.enums import AuthLevel


class ITDException(Exception):
    code: str | None = None  # ['error']['code']
    message: str | None = None  # ['error']['message']
    status_code: int | None = None  # response status code
    res_check: Callable[[Response], bool] | None = None
    text_check: Callable[[str], bool] | None = None
    json_check: Callable[[dict], bool] | None = None
    text: str  # python error message

    def __str__(self) -> str:
        return self.text

    # instances listed in DEFAULT_ERRORS and passed to @endpoint are declarations: they only describe how to recognize the error.
    # matches() recognizes it in the response, prepare() builds the exception to raise
    def matches(self, res: Response, json: dict) -> bool:
        """Похож ли ответ на эту ошибку

        Args:
            res (Response): Ответ
            json (dict): Тело ответа

        Returns:
            bool: Совпадение
        """
        error = cast(dict, json.get('error')) if isinstance(json.get('error'), dict) else {}
        return bool(
            (self.res_check and self.res_check(res))
            or (self.text_check and self.text_check(res.text))
            or (self.json_check and self.json_check(json))
            or (self.status_code is not None and res.status_code == self.status_code)
            or (self.code is not None and error.get('code') == self.code)
            or (self.message is not None and error.get('message') == self.message)
        )

    def prepare(self, json: dict) -> 'ITDException':
        exception = self.__class__.__new__(self.__class__)
        BaseException.__init__(exception, *self.args)
        exception.__dict__.update(self.__dict__)
        exception._fill(json.get('error') if isinstance(json.get('error'), dict) else {})
        return exception

    def _fill(self, error: dict) -> None:
        pass


class ValidateError(ITDException):
    pass


class ValidationError(ValidateError):
    text = 'Failed validation'
    code = 'VALIDATION_ERROR'
    status_code = 422
    json_check = staticmethod(lambda json: 'found' in json)

    def _fill(self, error: dict) -> None:
        self.text = error.get('message', 'Failed validation')


class RateLimitError(ITDException):
    code = 'RATE_LIMIT_EXCEEDED'
    json_check = staticmethod(lambda json: json.get('error') == 'Too Many Requests')

    def __init__(self, retry_after: int = 0):
        self.retry_after = retry_after

    def _fill(self, error: dict) -> None:
        self.retry_after = error.get('retryAfter', 0)

    def __str__(self) -> str:
        if self.retry_after:
            return f'Rate limit exceeded - too much requests. Retry after {self.retry_after} seconds'
        return 'Rate limit exceeded - too much requests'


class NotFoundError(ITDException):
    code = 'NOT_FOUND'

    def __init__(
        self, obj: str, message: str | None = None, json_check: Callable[[dict], bool] | None = None, res_check: Callable[[Response], bool] | None = None
    ):
        self.text = f'{obj} not found'
        self.json_check = json_check
        self.res_check = res_check
        if message:
            self.message = message
        if obj == 'Profile':
            self.code = 'PROFILE_NOT_FOUND'


class TooLargeError(ITDException):
    def __init__(self, obj: str, code: int = 414):
        self.status_code = code
        self.text = f'{obj} is too large'


class AuthError(ITDException):
    text = ''

    def __str__(self):
        return f'Failed to auth: {self.text}'


class SessionNotFoundError(AuthError):
    code = 'SESSION_NOT_FOUND'
    text = 'Session not found (invalid refresh token)'


class RefreshTokenMissingError(AuthError):
    code = 'REFRESH_TOKEN_MISSING'
    text = 'No refresh token (possible SDK issue). If you see this, report problem at https://github.com/itd-sdk/itd-sdk/issues/new'


class SessionExpiredError(AuthError):
    code = 'SESSION_EXPIRED'
    text = 'Session expired'


class UnauthorizedError(AuthError):
    code = 'UNAUTHORIZED'
    text = 'Unauthorized (access not passed or not valid)'


class InvalidAccessTokenError(AuthError):
    text = 'Invalid access token'
    text_check = staticmethod(lambda text: text == 'UNAUTHORIZED')
    json_check = staticmethod(lambda json: json.get('error') in ('invalid signature', 'invalid token'))


class JWTAlgorithmUnsupportedError(AuthError):
    json_check = staticmethod(lambda json: json.get('error') == 'Unsupported token algorithm')
    text = 'Access token JWT algorithm unsupported'


class SessionRevokedError(AuthError):
    code = 'SESSION_REVOKED'
    text = 'Session revoked (logged out)'


class AccessTokenExpiredError(AuthError):
    text = 'Token expired'
    json_check = staticmethod(lambda json: json.get('error') == 'token expired' or json.get('message') == 'Invalid or expired token')


class LoginError(AuthError):
    pass


class InvalidCredentialsError(LoginError):
    code = 'INVALID_CREDENTIALS'
    text = 'Invalid login credentials'


class CaptchaFailedError(LoginError):
    code = 'TURNSTILE_VERIFICATION_FAILED'
    text = 'Captcha check failed. Please fill issue at https://github.com/itd-sdk/itd-sdk/issues/new'


class EmailDomainNotAllowedError(LoginError):
    code = 'ACCOUNT_EMAIL_DOMAIN_NOT_ALLOWED'
    text = 'Email domain not allowed'


class InvalidEmailError(LoginError):
    code = 'INVALID_EMAIL'
    text = 'Invalid email format'


class PasswordError(ITDException):
    pass


class SamePasswordError(PasswordError, ValidateError):
    code = 'SAME_PASSWORD'
    text = 'Old and new password must not equals'


class InvalidOldPasswordError(PasswordError):
    code = 'INVALID_OLD_PASSWORD'
    text = 'Old password is incorrect'


class InvalidPasswordError(PasswordError, ValidateError):
    code = 'INVALID_PASSWORD'
    text = 'Password requirement not met'


class NoRightsError(ITDException):
    pass


class InsufficientAuthLevelError(NoRightsError):
    def __init__(self, current: AuthLevel, requires: AuthLevel):
        self.text = f'Insufficient auth level (current is {current.name}, requires {requires.name})'


class PinNotOwnedError(NoRightsError):
    code = 'PIN_NOT_OWNED'
    text = 'You do not own this pin'


class ForbiddenError(NoRightsError):
    code = 'FORBIDDEN'

    # message = 'Некоторые файлы не принадлежат вам'
    def __init__(self, action: str):
        self.text = f'forbidden to {action}'


class RequiresVerificationError(NoRightsError):
    code = 'GIF_REQUIRES_VERIFICATION'

    def __init__(self, obj: str):
        self.text = f'{obj} allowed only for verificated users'


class RequiresSubscriptionError(NoRightsError):
    code = 'VIDEO_REQUIRES_NUKSTA'

    def __init__(self, obj: str):
        self.text = f'{obj} allowed only for users with НУКСТА subscription'


class UsernameTakenError(ValidateError):
    code = 'USERNAME_TAKEN'
    text = 'Username is already taken'


class InvalidDisplayNameError(ValidateError):
    code = 'INVALID_DISPLAY_NAME'
    text = 'Invalid display name'


class YourselfError(ITDException):
    pass


class CantFollowYourselfError(YourselfError):
    message = text = 'Cannot follow yourself'


class CantRepostYourselfError(YourselfError):
    message = text = 'Cannot repost your own post'


class CantBlockYourselfError(YourselfError):
    message = text = 'Cannot block yourself'


class AlreadyError(ITDException):
    pass


class AlreadyRepostedError(AlreadyError):
    code = 'CONFLICT'
    text = 'Post already reposted'


class AlreadyReportedError(AlreadyError):
    message = 'Вы уже отправляли жалобу на этот контент'
    text = 'Object already reported'


class AlreadyFollowingError(AlreadyError):
    code = 'CONFLICT'
    text = 'Already following user'


class AlreadyDeletedError(AlreadyError):
    code = 'ALREADY_DELETED'

    def __init__(self, obj: str):
        self.text = f'{obj} already deleted'
        if obj == 'Comment':
            self.res_check = lambda res: res.status_code == 500 and res.text == 'Комментарий не найден'


class AlreadyBlockedError(AlreadyError):
    code = 'CONFLICT'
    text = 'User already blocked'


class PollError(ITDException):
    pass


class OptionsNotBelongError(PollError):
    message = 'Один или несколько вариантов не принадлежат этому опросу'
    text = 'One or more options do not belong to poll'


class NotMultipleChoiceError(PollError):
    message = 'В этом опросе можно выбрать только один вариант'
    text = 'Only one option can be choosen in this poll'


class FileError(ITDException):
    pass


class InvalidFileTypeError(FileError):
    # code = 'VALIDATION_ERROR'
    message = 'Недопустимый тип файла'
    text = 'Invalid file extension'


class UploadError(FileError):
    code = 'UPLOAD_ERROR'
    text = 'Failed to upload file (unknown reason)'


class ModerationFailedError(FileError):
    code = 'CONTENT_MODERATION_ERROR'
    text = 'Unable to moderate image'


class EditExpiredError(ITDException):
    code = 'EDIT_WINDOW_EXPIRED'
    text = 'Editing allowed only in first 48 hours after posting'


class NotDeletedError(ITDException):
    code = 'NOT_DELETED'

    def __init__(self, obj: str):
        self.text = f'{obj} is not deleted'


class NotBlockedError(ITDException):
    code = 'CONFLICT'
    text = 'User is not blocked'


class UserBlockedError(ITDException):
    code = 'BLOCKED'
    text = 'User blocked (by you or by him)'


class NotPinnedError(ITDException):
    code = 'NOT_PINNED'
    text = 'Post not found or is not pinned'


class InternalError(ITDException):
    status_code = 502
    code = 'INTERNAL_ERROR'
    text = 'Internal server error'


class BannedWordError(ITDException):
    code = 'BANNED_WORD'

    def __init__(self, obj: str) -> None:
        self.text = f'{obj} contains prohibited content'


class TargetUserBannedError(ITDException):  # target banned (eg if you try to follow banned user)
    message = 'Этот аккаунт заблокирован'
    text = 'Target user has been deactivated'


class AccountBannedError(LoginError):  # you are banned
    json_check = staticmethod(lambda json: json.get('error', {}).get('code') in ('ACCOUNT_BANNED', 'ACCOUNT_DEACTIVATED'))
    text = 'Account has been deactivated'


class AccountTemporarilyBannedError(LoginError):
    code = 'ACCOUNT_DEACTIVATED'
    text = 'Account has been temporarily deactivated'


class ProfileRequiredError(ITDException):
    code = 'PROFILE_REQUIRED'
    text = 'No profile. Please create your profile first'


class AccountDeletedError(ITDException):
    code = 'ACCOUNT_DELETED'
    text = 'Account has been deleted'
    can_restore: bool = True
    restore_deadline: datetime | None = None

    def _fill(self, error: dict) -> None:
        self.can_restore = error.get('canRestore', True)


class QRError(ITDException):
    pass


class QRApproverNotAllowed(QRError):
    code = 'QR_APPROVER_NOT_ALLOWED'
    text = 'QR approving allowed only for mobile devices'


class EventError(ITDException):
    pass


class ItemNotFoundError(EventError):
    code = 'ITEM_UNAVAILABLE'
    text = 'Inventory item not found or wrong type'


DEFAULT_ERRORS = (
    RateLimitError(),
    InvalidAccessTokenError(),
    UnauthorizedError(),
    JWTAlgorithmUnsupportedError(),
    AccessTokenExpiredError(),
    AccountBannedError(),
    AccountTemporarilyBannedError(),
    InternalError(),
    ProfileRequiredError(),
    RefreshTokenMissingError(),
    AccountDeletedError()
)
