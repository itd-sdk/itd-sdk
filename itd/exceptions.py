class ITDException(Exception):
    code: str | None = None # ['error']['code']
    message: str | None = None # ['error']['message']
    status_code: int | None = None # response status code

    text: str # python error message

    def __str__(self) -> str:
        return self.text


class ValidateError(ITDException): pass

class ValidationError(ValidateError):
    text = 'Failed validation'
    code = 'VALIDATION_ERROR'

class RateLimitError(ITDException):
    code = 'RATE_LIMIT_EXCEEDED'
    def __init__(self, retry_after: int = 0):
        self.retry_after = retry_after
    def __str__(self) -> str:
        return f'Rate limit exceeded - too much requests. Retry after {self.retry_after} seconds'


class NotFoundError(ITDException):
    code = 'NOT_FOUND'
    def __init__(
        self,
        obj: str,
        message: str | None = None,
        _reply_comment_user_not_found: bool = False,
        _subscription_not_found: bool = False,
        _hashtag_not_found: bool = False,
        _liked_posts_user_not_found: bool = False,
        _report_target_not_found: bool = False,
        _notification_read_error: bool = False
    ):
        self.text = f'{obj} not found'
        if message:
            self.message = message
        if obj == 'Profile':
            self.code = 'PROFILE_NOT_FOUND'
        self._reply_comment_user_not_found = _reply_comment_user_not_found
        self._subscription_not_found = _subscription_not_found
        self._hashtag_not_found = _hashtag_not_found
        self._liked_posts_user_not_found = _liked_posts_user_not_found
        self._report_target_not_found = _report_target_not_found
        self._notification_read_error = _notification_read_error

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
    text = 'UnauthorizedError (possible SDK issue). If you see this, report problem at https://github.com/itd-sdk/itd-sdk/issues/new'

class InvalidAccessTokenError(AuthError):
    text = 'Invalid access token'

class SessionRevokedError(AuthError):
    code = 'SESSION_REVOKED'
    text = 'Session revoked (logged out)'

class AccessTokenExpiredError(AuthError):
    text = 'Token expired'


class PasswordError(ITDException): pass

class SamePasswordError(PasswordError, ValidateError):
    code = 'SAME_PASSWORD'
    text = 'Old and new password must not equals'

class InvalidOldPasswordError(PasswordError):
    code = 'INVALID_OLD_PASSWORD'
    text = 'Old password is incorrect'

class InvalidPasswordError(PasswordError, ValidateError):
    code = 'INVALID_PASSWORD'
    text = 'Password requirement not met'


class NoRightsError(ITDException): pass

class InsufficientAuthLevelError(NoRightsError):
    def __init__(self) :
        self.text = 'Insufficient auth level'

class PinNotOwnedError(NoRightsError):
    code = "PIN_NOT_OWNED"
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


class UsernameTakenError(ValidateError):
    code = 'USERNAME_TAKEN'
    text = 'Username is already taken'

class InvalidDisplayNameError(ValidateError):
    code = 'INVALID_DISPLAY_NAME'
    text = 'Invalid display name'


class YourselfError(ITDException): pass

class CantFollowYourselfError(YourselfError):
    message = text = 'Cannot follow yourself'

class CantRepostYourselfError(YourselfError):
    message = 'Cannot repost your own post'
    text = 'Cannot repost your own post'

class CantBlockYourselfError(YourselfError):
    message = text = 'Cannot block yourself'


class AlreadyError(ITDException): pass

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
    def __init__(self, obj: str, _delete_comment_not_found: bool = False):
        self.text = f'{obj} already deleted'
        self._delete_comment_not_found = _delete_comment_not_found

class AlreadyBlockedError(AlreadyError):
    code = 'CONFLICT'
    text = 'User already blocked'


class PollError(ITDException): pass

class OptionsNotBelongError(PollError):
    message = 'Один или несколько вариантов не принадлежат этому опросу'
    text = 'One or more options do not belong to poll'

class NotMultipleChoiceError(PollError):
    message = 'В этом опросе можно выбрать только один вариант'
    text = 'Only one option can be choosen in this poll'


class FileError(ITDException): pass

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
    code = 'INTERNAL_ERROR'
    text = 'Internal server error'

class BannedWordError(ITDException):
    code = 'BANNED_WORD'
    def __init__(self, obj: str) -> None:
        self.text = f'{obj} contains prohibited content'

class TargetUserBannedError(ITDException): # target banned (eg if you try to follow banned user)
    message = 'Этот аккаунт заблокирован'
    text = 'Target user has been deactivated'

class AccountBannedError(ITDException): # you are banned
    code = 'ACCOUNT_BANNED'
    text = 'Account has been deactivated'

class ProfileRequiredError(ITDException):
    code = 'PROFILE_REQUIRED'
    text = 'No profile. Please create your profile first'


DEFAULT_ERRORS = (RateLimitError(), InvalidAccessTokenError(), UnauthorizedError(), AccessTokenExpiredError(), AccountBannedError(), InternalError(), ProfileRequiredError())
