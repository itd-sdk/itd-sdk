import pytest

from itd.post import Post
from itd.user import Me


POST_ID = '0fe47f03-3fda-4d95-a0f0-8bc0f950df8a'


def test_post_author_inherits_client(client2):
    post = Post(POST_ID, client2)
    assert post.author._client is client2


def test_post_comments_inherit_client(client2):
    post = Post(POST_ID, client2)
    post.comments.load(3)
    assert post.comments._client is client2


def test_post_comment_items_inherit_client(client2):
    post = Post(POST_ID, client2)
    post.comments.load(3)
    for comment in post.comments:
        assert comment._client is client2


def test_post_poll_inherits_client(client2):
    # find a post with poll or skip
    post = Post(POST_ID, client2)
    if post.poll is None:
        pytest.skip('Post has no poll')
    assert post.poll._client is client2


def test_me_subscription_inherits_client(client2):
    me = Me(client2)
    assert me.subscription._client is client2


def test_me_privacy_inherits_client(client2):
    me = Me(client2)
    assert me.privacy._client is client2


def test_me_profile_inherits_client(client2):
    me = Me(client2)
    assert me.profile._client is client2


def test_two_clients_are_independent(client, client2):
    post1 = Post(POST_ID, client)
    post2 = Post(POST_ID, client2)
    assert post1._client is client
    assert post2._client is client2
    assert post1._client is not post2._client
