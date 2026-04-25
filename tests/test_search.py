from itd.user import User
from itd.hashtag import Hashtag


def test_search_returns_tuple(client):
    users, hashtags = client.search('итд')
    assert isinstance(users, list)
    assert isinstance(hashtags, list)


def test_search_users_are_users(client):
    users, _ = client.search('итд')
    for u in users:
        assert isinstance(u, User)


def test_search_hashtags_are_hashtags(client):
    _, hashtags = client.search('итд')
    for h in hashtags:
        assert isinstance(h, Hashtag)


def test_search_respects_limits(client):
    users, hashtags = client.search('a', users_limit=2, hashtags_limit=3)
    assert len(users) <= 2
    assert len(hashtags) <= 3
