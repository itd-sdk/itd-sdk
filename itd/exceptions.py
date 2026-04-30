class ITDException(Exception):
    code: str | None = None # ['error']['code']
    message: str | None = None # ['error']['message']
    status_code: int | None = None # response status code

    text: str # python error message

    def __str__(self) -> str:
        return self.text


class AuthError(ITDException):
    text = ''
    def __str__(self):
        return f'Failed to auth: {self.text}'

class SessionNotFound(AuthError):
    code = 'SESSION_NOT_FOUND'
    text = 'Session not found (invalid refresh token)'

class RefreshTokenMissing(AuthError):
    code = 'REFRESH_TOKEN_MISSING'
    text = 'No refresh token (possible SDK issue). If you see this, report problem at https://github.com/itd-sdk/itd-sdk/issues/new'

class SessionExpired(AuthError):
    code = 'SESSION_EXPIRED'
    text = 'Session expired'

class Unauthorized(AuthError):
    code = 'UNAUTHORIZED'
    text = 'Unauthorized (possible SDK issue). If you see this, report problem at https://github.com/itd-sdk/itd-sdk/issues/new'

class InvalidAccessToken(AuthError):
    text = 'Invalid access token'

class SessionRevoked(AuthError):
    code = 'SESSION_REVOKED'
    text = 'Session revoked (logged out)'

class AccessTokenExpired(AuthError):
    text = 'Token expired'

class SamePassword(ITDException):
    code = 'SAME_PASSWORD'
    text = 'Old and new password must not equals'

class InvalidOldPassword(ITDException):
    code = 'INVALID_OLD_PASSWORD'
    text = 'Old password is incorrect'

class InvalidPassword(ITDException):
    code = 'INVALID_PASSWORD'
    text = 'Password requirement not met'

class NotFound(ITDException):
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

class InsufficientAuthLevelError(ITDException):
    def __init__(self) :
        self.text = 'Insufficient auth level'

class ValidationError(ITDException):
    text = 'Failed validation'
    code = 'VALIDATION_ERROR'

class RateLimitExceeded(ITDException):
    code = 'RATE_LIMIT_EXCEEDED'
    def __init__(self, retry_after: int = 0):
        self.retry_after = retry_after
    def __str__(self) -> str:
        return f'Rate limit exceeded - too much requests. Retry after {self.retry_after} seconds'

class Forbidden(ITDException):
    code = 'FORBIDDEN'
    # message = 'Некоторые файлы не принадлежат вам'
    def __init__(self, action: str):
        self.text = f'Forbidden to {action}'

class UsernameTaken(ITDException):
    code = 'USERNAME_TAKEN'
    text = 'Username is already taken'

class CantFollowYourself(ITDException):
    message = text = 'Cannot follow yourself'

class CantRepostYourPost(ITDException):
    message = 'Cannot repost your own post'
    text = 'Cannot repost your own post'

class AlreadyReposted(ITDException):
    code = 'CONFLICT'
    text = 'Post already reposted'

class AlreadyReported(ITDException):
    message = 'Вы уже отправляли жалобу на этот контент'
    text = 'Object already reported'

class TooLarge(ITDException):
    def __init__(self, obj: str, code: int = 414):
        self.status_code = code
        self.text = f'{obj} is too large'

class PinNotOwned(ITDException):
    code = "PIN_NOT_OWNED"
    text = 'You do not own this pin'

class AlreadyFollowing(ITDException):
    code = 'CONFLICT'
    text = 'Already following user'

class AccountBanned(ITDException): # you banned
    code = 'ACCOUNT_BANNED'
    text = 'Account has been deactivated'

class TargetUserBanned(ITDException): # target banned (eg if you try to follow banned user)
    message = 'Этот аккаунт заблокирован'
    text = 'Target user has been deactivated'

class OptionsNotBelong(ITDException):
    message = 'Один или несколько вариантов не принадлежат этому опросу'
    text = 'One or more options do not belong to poll'

class NotMultipleChoice(ITDException):
    message = 'В этом опросе можно выбрать только один вариант'
    text = 'Only one option can be choosen in this poll'

class ProfileRequired(ITDException):
    code = 'PROFILE_REQUIRED'
    text = 'No profile. Please create your profile first'

class RequiresVerification(ITDException):
    code = 'VIDEO_REQUIRES_VERIFICATION'
    def __init__(self, obj: str):
        self.text = f'{obj} allowed only for verificated users'

class InvalidFileType(ITDException):
    # code = 'VALIDATION_ERROR'
    message = 'Недопустимый тип файла'
    text = 'Invalid file extension'

class EditExpired(ITDException):
    code = 'EDIT_WINDOW_EXPIRED'
    text = 'Editing allowed only in first 48 hours after posting'

class UploadError(ITDException):
    code = 'UPLOAD_ERROR'
    text = 'Failed to upload file (unknown reason)'

class NotDeleted(ITDException):
    code = 'NOT_DELETED'
    def __init__(self, obj: str):
        self.text = f'{obj} is not deleted'

class AlreadyDeleted(ITDException):
    code = 'ALREADY_DELETED'
    def __init__(self, obj: str, _delete_comment_not_found: bool = False):
        self.text = f'{obj} already deleted'
        self._delete_comment_not_found = _delete_comment_not_found

class AlreadyBlocked(ITDException):
    code = 'CONFLICT'
    text = 'User already blocked'

class NotBlocked(ITDException):
    code = 'CONFLICT'
    text = 'User is not blocked'

class CantBlockYourself(ITDException):
    message = text = 'Cannot block yourself'

class UserBlocked(ITDException):
    code = 'BLOCKED'
    text = 'User blocked (by you or by him)'

class NotPinned(ITDException):
    code = 'NOT_PINNED'
    text = 'Post not found or is not pinned'

class InternalError(ITDException):
    code = 'INTERNAL_ERROR'
    text = 'Internal server error'

class InvalidDisplayName(ITDException):
    code = 'INVALID_DISPLAY_NAME'
    text = 'Invalid display name'

class ModerationFailed(ITDException):
    code = 'CONTENT_MODERATION_ERROR'
    text = 'Unable to moderate image'


DEFAULT_ERRORS = (InvalidAccessToken(), RateLimitExceeded(), Unauthorized(), AccessTokenExpired(), AccountBanned())
