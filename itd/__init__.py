#                      ######################              ####
####               ##   ######################           ########
####             ####            ####                   ####  ####
####           ######            ####                  ####    ####
####          #######            ####                 ####      ####
####        #########            ####                ####        ####
####      #####  ####            ####               ####          ####
####    #####    ####            ####              ####            ####
####  #####      ####            ####             ####              ####
#########        ####            ####            ####                ####            +----  +----\   |  /
#######          ####            ####       ##################################       |      |     |  | /
#####            ####            ####      ####################################  -   +---+  |     |  ++
###              ####            ####      ####                            ####          |  |     |  | \
#                ####            ###       ####                            ####      ----+  +----/   |  \
"""
iii     iii tttttttttt   ddddddddd       |
iii   iiiii     ttt      ddd   ddd
iii iii iii     ttt      ddd   ddd
iiiii   iii     ttt    ddddddddddddddd
iiii    iii     ttt    dd           dd

    ssssssss  dddddddd    kkk   kkk
   sss        ddd   ddd   kkk   kkk
   sss        ddd    ddd  kkk   kkk
     sssssss  ddd    ddd  kkk  kkk
         sss  ddd    ddd  kkkkkk
         sss  ddd   ddd   kkk  kkk
    ssssss    dddddddd    kkk   kkk

                          by fi.res
                    @fdg | @itd_sdk
"""

from importlib.metadata import version
from time import sleep

__version__ = version('itd-sdk')

from itd.core.client import Client as ITDClient
from itd.core.client import init_client
from itd.core.config import Config as ITDConfig
from itd.core.default import LimiterConfig, limiters
from itd.core.default import set_config as set_limiter_config
from itd.core.limiter import BurstRateLimiter, HalfRateLimiter, IPRateLimiter, RateLimiter
from itd.models.announcement import Announcement, Announcements
from itd.models.clan import Clan, TopClans
from itd.models.comment import Comment
from itd.models.file import File
from itd.models.hashtag import Hashtag, Hashtags
from itd.models.notification import Notification, Notifications, Ntf, Ntfs
from itd.models.poll import NewPoll
from itd.models.portal import Portal
from itd.models.post import HashtagPosts, LikedPosts, Post, Posts, UserPosts
from itd.models.search import Search
from itd.models.session import Sessions
from itd.models.user import Me, User, Users, WhoToFollow, get_follow_status
from itd.models.version import Apps, Changelog


# call if you set auto_acquire=False in the end of cycle
def acquire_limiters():
    sleep(max((limiter.delay for limiter in limiters.values() if limiter.used), default=0))

    for limiter in limiters.values():
        limiter.used = False


__all__ = [
    '__version__',
    'Changelog',
    'Apps',
    'ITDClient',
    'ITDConfig',
    'init_client',
    'Comment',
    'Clan',
    'TopClans',
    'File',
    'Announcement',
    'Announcements',
    'Hashtag',
    'Hashtags',
    'Notifications',
    'Notification',
    'Ntfs',
    'Ntf',
    'Post',
    'Posts',
    'UserPosts',
    'HashtagPosts',
    'LikedPosts',
    'NewPoll',
    'Sessions',
    'User',
    'Me',
    'Users',
    'Portal',
    'WhoToFollow',
    'Search',
    'get_follow_status',
    'set_limiter_config',
    'LimiterConfig',
    'BurstRateLimiter',
    'RateLimiter',
    'HalfRateLimiter',
    'IPRateLimiter',
    'acquire_limiters'
]
