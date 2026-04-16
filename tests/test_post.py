from pytest import fixture

from itd.post import Post
from itd.exceptions import NotFound


@fixture(scope="module")
def owned_post(client):
    post = Post.new('test post', client=client)
    yield post
    try:
        post.delete(client)
    except NotFound:
        pass


def test_post_loads(redis_post):
    assert redis_post.content is not None
    assert redis_post.author is not None
    assert redis_post.created_at is not None
    assert redis_post._loaded


def test_post_refresh(redis_post):
    redis_post.refresh()
    assert redis_post._loaded



def test_view(redis_post):
    redis_post.view()


def test_like_updates_state(redis_post):
    redis_post.unlike()
    before = redis_post.likes_count
    redis_post.like()
    assert redis_post.is_liked
    assert redis_post.likes_count == before + 1


def test_unlike_updates_state(redis_post):
    redis_post.like()
    before = redis_post.likes_count
    redis_post.unlike()
    assert not redis_post.is_liked
    assert redis_post.likes_count == before - 1


def test_repost_updates_state(client, client2):
    post = Post.new('тест репост', client=client)

    before = post.reposts_count
    reposted = post.repost(client=client2)

    assert post.is_reposted
    assert post.reposts_count == before + 1
    assert reposted.original_post is not None
    assert reposted.original_post.id == post.id

    reposted.delete(client2)
    post.delete(client)


def test_edit_updates_state(owned_post):
    assert owned_post.edited_at is None
    updated_at = owned_post.edit('тест изменен')
    assert owned_post.content == 'тест изменен'
    assert owned_post.edited_at == updated_at
    assert owned_post.edited_at is not None


def test_add_comment_increments_count(owned_post, client):
    before = owned_post.comments_count
    comment = owned_post.add_comment('тест комментарий', client=client)
    assert owned_post.comments_count == before + 1
    assert comment is not None


def test_pin_unpin_updates_state(owned_post, client):
    previously_pinned_id = client.user.pinned_post_id

    owned_post.pin(client)
    assert owned_post.is_pinned

    owned_post.unpin(client)
    assert not owned_post.is_pinned

    if previously_pinned_id:
        Post(previously_pinned_id).pin(client)


def test_delete_restore(client):
    post = Post.new('test 2', client=client)

    post.delete(client)
    post.restore(client)

    post.refresh()
    assert post._loaded

    post.delete(client)
