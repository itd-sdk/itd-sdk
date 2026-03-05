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

class SamePassword(Exception):
    def __str__(self):
        return 'Old and new password must not equals'

class InvalidOldPassword(Exception):
    def __str__(self):
        return 'Old password is incorrect'

class NotFound(Exception):
    def __init__(self, obj: str):
        self.obj = obj
    def __str__(self):
        return f'{self.obj} not found'

class NotFoundOrForbidden(Exception):
    def __init__(self, obj: str):
        self.obj = obj
    def __str__(self):
        return f'{self.obj} not found or access denied'


class UserBanned(Exception):
    def __str__(self):
        return 'User banned'

class ValidationError(Exception):
    # def __init__(self, name: str, value: str):
    #     self.name = name
    #     self.value = value
    def __str__(self):
        return 'Failed validation'# on {self.name}: "{self.value}"'

class PendingRequestExists(Exception):
    def __str__(self):
        return 'Pending verifiaction request already exists'

class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
    def __str__(self):
        return f'Rate limit exceeded - too much requests. Retry after {self.retry_after} seconds'

class Forbidden(Exception):
    def __init__(self, action: str):
        self.action = action
    def __str__(self):
        return f'Forbidden to {self.action}'

class UsernameTaken(Exception):
    def __str__(self):
        return 'Username is already taken'

class CantFollowYourself(Exception):
    def __str__(self):
        return 'Cannot follow yourself'

class Unauthorized(Exception):
    def __str__(self):
        return 'Auth required - refresh token'

class CantRepostYourPost(Exception):
    def __str__(self):
        return 'Cannot repost your own post'

class AlreadyReposted(Exception):
    def __str__(self):
        return 'Post already reposted'

class AlreadyReported(Exception):
    def __init__(self, obj: str) -> None:
        self.obj = obj
    def __str__(self):
        return f'{self.obj} already reported'

class TooLarge(Exception):
    def __str__(self):
        return 'Search query too large'

class PinNotOwned(Exception):
    def __init__(self, pin: str) -> None:
        self.pin = pin
    def __str__(self):
        return f'You do not own "{self.pin}" pin'

class NoContent(Exception):
    def __str__(self) -> str:
        return 'Content or attachments required'

class AlreadyFollowing(Exception):
    def __str__(self) -> str:
        return 'Already following user'

class AccountBanned(Exception):
    def __str__(self) -> str:
        return 'Account has been deactivated'

class OptionsNotBelong(Exception):
    def __str__(self) -> str:
        return 'One or more options do not belong to poll'

class NotMultipleChoice(Exception):
    def __str__(self) -> str:
        return 'Only one option can be choosen in this poll'

class EmptyOptions(Exception):
    def __str__(self) -> str:
        return 'Options cannot be empty (pre-validation)'

class ProfileRequired(Exception):
    def __str__(self) -> str:
        return 'No profile. Please create your profile first'

class VideoRequiresVerification(Exception):
    def __str__(self) -> str:
        return 'Video uploading allowed only for verificated users'

class InvalidFileType(Exception):
    def __str__(self) -> str:
        return 'Invalid file extension'