from time import sleep

import pytest

from itd.post import Post
from itd.exceptions import NotFound


@pytest.fixture(autouse=True)
def _rate_limit():
    yield
    sleep(0.5)


@pytest.fixture
def comments(redis_post):
    redis_post.comments.clear()
    redis_post.comments._total = None
    redis_post.comments.has_more = True
    return redis_post.comments


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
