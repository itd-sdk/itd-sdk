from itd.hashtag import Hashtag


def test_hashtag_strips_hash(client):
    h = Hashtag('#test', client)
    assert h.name == 'test'


def test_hashtag_without_hash(client):
    h = Hashtag('test', client)
    assert h.name == 'test'


def test_hashtag_refresh_loads_fields(client):
    h = Hashtag('итд', client)
    h.refresh()
    assert h.id is not None
    assert isinstance(h.posts_count, int)
    assert h.posts_count >= 0
