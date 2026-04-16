import pytest

from itd.post import Post
from itd.comment import Comment
from itd.exceptions import NotFound


@pytest.fixture
def comments(redis_post):
    redis_post.comments.clear()
    redis_post.comments._total = None
    redis_post.comments.has_more = True
    return redis_post.comments


@pytest.fixture(scope="module")
def owned_post(client):
    post = Post.new('test post (comments)', client=client)
    yield post
    try:
        post.delete(client)
    except NotFound:
        pass


@pytest.fixture
def comment(owned_post, client):
    c = owned_post.add_comment('тест коммент', client=client)
    yield c
    try:
        c.delete(client)
    except NotFound:
        pass


def test_comments_load(comments):
    comments.load(3)
    assert len(comments) == 3


def test_comments_load_all(comments):
    comments.load_all()
    assert len(comments) == comments.total
    assert not comments.has_more


def test_comments_has_more(comments):
    assert comments.has_more
    comments.load(1)
    assert comments.has_more


def test_comments_refresh(comments):
    comments.load(5)
    comments.refresh(2)
    assert len(comments) == 2


def test_comment_like_increments(comment, client2):
    before = comment.likes_count
    count = comment.like(client2)
    assert count == before + 1
    assert comment.likes_count == before + 1
    comment.unlike(client2)


def test_comment_unlike_decrements(comment, client2):
    comment.like(client2)
    before = comment.likes_count
    count = comment.unlike(client2)
    assert count == before - 1
    assert comment.likes_count == before - 1


def test_comment_reply_creates_reply(comment, client2):
    reply = comment.reply('ответ', client=client2)
    assert reply.id is not None
    assert reply.content == 'ответ'
    reply.delete(client2)


def test_comment_delete(owned_post, client):
    c = owned_post.add_comment('делет', client=client)
    c.delete(client)


def test_comment_new_adds_to_post(owned_post, client):
    comment = Comment.new(owned_post.id, 'напрямую через Comment.new', client=client)
    assert comment.id is not None
    assert comment.content == 'напрямую через Comment.new'
    comment.delete(client)


def test_comment_str(comment):
    assert str(comment) == comment.content


def test_comment_has_author(comment, client):
    assert comment.author is not None
    assert comment.author.id == client.user_id
