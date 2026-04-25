class ITDException(Exception):
    code: str | None = None # ['error']['code']
    message: str | None = None # ['error']['message']
    status_code: int | None = None # response status code

    text: str # python error message

    def __str__(self) -> str:
        return self.text


class NoCookie(Exception):
    def __str__(self):
        return 'No cookie for refresh-token required action'

class NoAuthData(Exception):
    def __str__(self):
        return 'No auth data. Provide token or cookies'

class InvalidCookie(Exception):
    def __init__(self, code: str):
        self.code = code
    def __str__(self):
        if self.code == 'SESSION_NOT_FOUND':
            return 'Invalid cookie data: Session not found (incorrect refresh token)'
        elif self.code == 'REFRESH_TOKEN_MISSING':
            return 'Invalid cookie data: No refresh token'
        elif self.code == 'SESSION_EXPIRED':
            return 'Invalid cookie data: Session expired'
        # SESSION_REVOKED
        return 'Invalid cookie data: Session revoked (logged out)'

class InvalidToken(Exception):
    def __str__(self):
        return 'Invalid access token'

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
        _report_target_not_found: bool = False
    ):
        self.text = f'{obj} not found'
        if message:
            self.message = message
        self._reply_comment_user_not_found = _reply_comment_user_not_found
        self._subscription_not_found = _subscription_not_found
        self._hashtag_not_found = _hashtag_not_found
        self._liked_posts_user_not_found = _liked_posts_user_not_found
        self._report_target_not_found = _report_target_not_found

class NotFoundOrForbidden(Exception):
    def __init__(self, obj: str):
        self.obj = obj
    def __str__(self):
        return f'{self.obj} not found or access denied'

class UserBanned(Exception):
    def __str__(self):
        return 'User banned'

class ValidationError(ITDException):
    text = 'Failed validation'
    code = 'VALIDATION_ERROR'

class PendingRequestExists(Exception):
    def __str__(self):
        return 'Pending verifiaction request already exists'

class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
    def __str__(self):
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

class Unauthorized(Exception):
    def __str__(self):
        return 'Auth required - refresh token'

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
    status_code = 414
    def __init__(self, obj: str):
        self.text = f'{obj} is too large'

class PinNotOwned(ITDException):
    code = "PIN_NOT_OWNED"
    text = 'You do not own this pin'

class AlreadyFollowing(ITDException):
    code = 'CONFLICT'
    text = 'Already following user'

class AccountBanned(Exception): # you banned
    def __str__(self) -> str:
        return 'Account has been deactivated'

class TargetUserBanned(Exception): # target banned (eg if you try to follow banned user)
    def __str__(self) -> str:
        return 'Target user has been deactivated'

class OptionsNotBelong(ITDException):
    message = 'Один или несколько вариантов не принадлежат этому опросу'
    text = 'One or more options do not belong to poll'

class NotMultipleChoice(ITDException):
    message = 'В этом опросе можно выбрать только один вариант'
    text = 'Only one option can be choosen in this poll'

class EmptyOptions(Exception):
    def __str__(self) -> str:
        return 'Options cannot be empty (pre-validation)'

class ProfileRequired(Exception):
    def __str__(self) -> str:
        return 'No profile. Please create your profile first'

class RequiresVerification(ITDException):
    code = 'VIDEO_REQUIRES_VERIFICATION'
    def __init__(self, obj: str):
        self.text = f'{obj} allowed only for verificated users'

class InvalidFileType(Exception):
    def __str__(self) -> str:
        return 'Invalid file extension'

class EditExpired(ITDException):
    code = 'EDIT_WINDOW_EXPIRED'
    text = 'Editing allowed only in first 48 hours after posting'

class UploadError(Exception):
    def __str__(self) -> str:
        return 'Failed to upload file'

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

class NotFoundOrBlocked(Exception):
    def __str__(self) -> str:
        return 'User not found or blocked'

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

class NotificationNotFoundOrNotBelongOrAlreadyRead(ITDException):
    text = 'Notification not found, not belong to you or already read'
    _notification_read_error = True