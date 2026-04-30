from __future__ import annotations
from uuid import UUID
from typing import TYPE_CHECKING

from itd.enums import Unset, UNSET, AccessType
from itd.exceptions import (
    NotFoundError, TooLargeError, ValidationError, RequiresVerificationError, UsernameTakenError, AlreadyFollowingError,
    AlreadyDeletedError, NotDeletedError, AlreadyBlockedError, NotBlockedError, CantFollowYourselfError, UserBlockedError,
    CantBlockYourselfError, TargetUserBannedError
)
from itd.base import catch_errors, rate_limit
if TYPE_CHECKING:
    from itd.client import Client

@rate_limit()
@catch_errors(NotFoundError('User'), TooLargeError('User'), NotFoundError('Profile'), TargetUserBannedError())
def get_user(client: Client, username_or_id: str | UUID):
    return client.request('get', f'users/{username_or_id}')

@rate_limit(None, 10, 25)
@catch_errors(ValidationError(), RequiresVerificationError('GIF banner uploading'), UsernameTakenError())
def update_profile(client: Client, bio: str | None = None, display_name: str | None = None, username: str | None = None, banner_id: UUID | Unset | None = None):
    data = {}
    if bio is not None:
        data['bio'] = bio
    if display_name:
        data['displayName'] = display_name
    if username:
        data['username'] = username
    if banner_id is not None:
        data['bannerId'] = str(banner_id) if banner_id != UNSET else None
    return client.request('put', 'users/me', data)

@rate_limit()
@catch_errors()
def get_profile(client: Client):
    return client.request('get', 'profile')

@rate_limit()
@catch_errors()
def get_privacy(client: Client):
    return client.request('get', 'users/me/privacy')

@rate_limit()
@catch_errors(ValidationError())
def update_privacy(client: Client, is_private: bool | None = None, wall_access: AccessType | None = None, likes_visibility: AccessType | None = None, show_last_seen: bool | None = None):
    data = {}
    if is_private is not None:
        data['isPrivate'] = is_private
    if wall_access:
        data['wallAccess'] = wall_access.value
    if likes_visibility:
        data['likesVisibility'] = likes_visibility.value
    if show_last_seen is not None:
        data['showLastSeen'] = show_last_seen
    return client.request('put', 'users/me/privacy', data)

@rate_limit(5, 30, 80)
@catch_errors(NotFoundError('User'), AlreadyFollowingError(), TooLargeError('Username'), CantFollowYourselfError(), UserBlockedError(), TargetUserBannedError())
def follow(client: Client, username_or_id: str | UUID):
    return client.request('post', f'users/{username_or_id}/follow')

@rate_limit()
@catch_errors(NotFoundError('User'), TooLargeError('Username'), TargetUserBannedError())
def unfollow(client: Client, username_or_id: str | UUID):
    return client.request('delete', f'users/{username_or_id}/follow')

@rate_limit()
@catch_errors(NotFoundError('User'), ValidationError(), TooLargeError('Username'), TargetUserBannedError())
def get_followers(client: Client, username_or_id: str | UUID, page: int = 1): # !! page not works if not me
    return client.request('get', f'users/{username_or_id}/followers', {'page': page})

@rate_limit()
@catch_errors(NotFoundError('User'), ValidationError(), TooLargeError('Username'), TargetUserBannedError())
def get_following(client: Client, username_or_id: str | UUID, page: int = 1): # !! page not works if not me
    return client.request('get', f'users/{username_or_id}/following', {'page': page})

@rate_limit()
@catch_errors(AlreadyDeletedError('Account'))
def delete_account(client: Client):
    return client.request('delete', 'users/me')

@rate_limit()
@catch_errors(NotDeletedError('Account'))
def restore_account(client: Client):
    return client.request('post', 'users/me/restore')

@rate_limit()
@catch_errors(NotFoundError('User'), TooLargeError('Username'), AlreadyBlockedError(), CantBlockYourselfError(), TargetUserBannedError())
def block(client: Client, username_or_id: str | UUID):
    return client.request('post', f'users/{username_or_id}/block')

@rate_limit()
@catch_errors(NotFoundError('User'), TooLargeError('Username'), NotBlockedError(), TargetUserBannedError())
def unblock(client: Client, username_or_id: str | UUID):
    return client.request('delete', f'users/{username_or_id}/block')

@rate_limit()
@catch_errors()
def get_blocked(client: Client, page: int = 1, limit: int = 20):
    return client.request('get', 'users/me/blocked', {'limit': limit, 'page': page})

@rate_limit()
@catch_errors()
def get_follow_status(client: Client, user_ids: list[UUID]):
    return client.request('post', 'users/follow-status', {'userIds': list(map(str, user_ids))})
