from unittest.mock import ANY, MagicMock, patch
from uuid import UUID

import pytest

from itd.core.default import set_default_client
from itd.enums import NotebookStyle
from itd.models.post import Post
from itd.models.utils import apply_marks, visible_marks

pytestmark = pytest.mark.usefixtures('keep_default_client')


def uid(n: int) -> str:
    return f'00000000-0000-0000-0000-{n:012d}'


POST_ID = uid(1)
ACTOR = {'id': uid(99), 'username': 'dezhurny', 'displayName': 'Дежурный', 'avatar': '🧽'}
TEXT = 'Сегодня мы пошли в школу 😀 Вообще ничего не понятно'
EVENTS = [{'id': 'aliceai', 'endsAt': '2099-01-01T00:00:00Z'}]


def mark(n: int, start: int, end: int, created: str = '2026-09-01T00:00:00Z') -> dict:
    return {'id': uid(n), 'start': start, 'end': end, 'eventId': 'aliceai', 'actor': ACTOR, 'createdAt': created}


CORRECTOR = {'revision': 'r1', 'events': EVENTS, 'marks': [mark(10, 11, 16)]}
RED_PEN = {
    'revision': 'r1',
    'events': EVENTS,
    'claims': [{'id': uid(20), 'eventId': 'aliceai', 'actor': ACTOR, 'isOwner': True}],
    # после эмодзи (2 единицы UTF-16) смещения сдвигаются
    'corrections': [{'id': uid(30), 'start': 28, 'end': 34, 'replacement': 'Ваще', 'createdAt': '2026-09-01T00:00:00Z'}],
}
POST_DATA = {
    'id': POST_ID,
    'author': {'id': uid(2), 'username': 'author', 'displayName': 'Автор', 'avatar': '😀'},
    'createdAt': '2026-09-01T00:00:00Z',
    'content': TEXT,
    'attachments': [],
    'notebook': {'style': 'ruled'},
    'corrector': CORRECTOR,
    'redPen': RED_PEN,
}


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.token = 'mock_token'
    client.config.load_on_getattr = False  # иначе отсутствующее поле перезагрузит пост из апи
    set_default_client(client)  # Comments() поста создается без клиента и берет дефолтный
    return client


@pytest.fixture
def post(mock_client):
    return Post.from_dict(POST_DATA, client=mock_client)


def test_post_fields(post):
    assert post.notebook == NotebookStyle.RULED
    assert len(post.correctors) == 1
    assert post.red_pens[0].replacement == 'Ваще'
    assert post.corrector.event_id == 'aliceai' and post.event_revision == 'r1'
    assert post.red_pen.my_claim is not None


def test_from_dict_sets_post_id(post):
    # from_dict без контекста (так строятся ленты и профили) не должен падать и должен знать свой пост
    assert post.corrector._post_id == UUID(POST_ID)
    assert post.correctors[0]._post_id == UUID(POST_ID)
    assert post.red_pen.claims[0]._post_id == UUID(POST_ID)


def test_repost_original_keeps_own_post_id(mock_client):
    original = {**POST_DATA, 'id': uid(5)}
    post = Post.from_dict({**POST_DATA, 'originalPost': original}, client=mock_client)
    assert post.corrector._post_id == UUID(POST_ID)
    assert post.original_post.corrector._post_id == UUID(uid(5))
    assert post.original_post.correctors[0]._post_id == UUID(uid(5))
    assert post.original_post.red_pen.claims[0]._post_id == UUID(uid(5))


def test_mask_content(post):
    # правка красной ручкой в текст не подставляется, только замазка
    assert post.mask_content() == 'Сегодня мы ■■■■■ в школу 😀 Вообще ничего не понятно'


def test_newer_red_pen_hides_mark(mock_client):
    corrector = {**CORRECTOR, 'marks': [mark(10, 0, 7, '2026-09-01T00:00:00Z'), mark(11, 8, 10, '2026-09-03T00:00:00Z')]}
    red_pen = {
        **RED_PEN,
        'corrections': [
            {'id': uid(30), 'start': 0, 'end': 7, 'replacement': 'Завтра', 'createdAt': '2026-09-02T00:00:00Z'},  # позже первой
            {'id': uid(31), 'start': 8, 'end': 10, 'replacement': 'вы', 'createdAt': '2026-09-02T00:00:00Z'},  # раньше второй
        ],
    }
    post = Post.from_dict({**POST_DATA, 'corrector': corrector, 'redPen': red_pen}, client=mock_client)
    assert [c.id for c in visible_marks(post.correctors, post.red_pens)] == [UUID(uid(11))]


def test_apply_marks(mock_client):
    corrector = {**CORRECTOR, 'marks': [mark(10, 0, 7), mark(11, 5, 13)]}
    post = Post.from_dict({**POST_DATA, 'corrector': corrector}, client=mock_client)
    assert apply_marks(TEXT, post.correctors) == '■■■■■■■ ■■ ■■шли в школу 😀 Вообще ничего не понятно'  # пересечение не ломает текст
    assert apply_marks('a b', []) == 'a b'


def test_apply_corrector_sends_operation_id(post, mock_client):
    with patch('itd.models.post.apply_corrector') as apply, patch('itd.models.post.CorrectorState.refresh'):
        try:
            post.apply_corrector(0, 7)
        except AssertionError:  # своей замазки в данных нет - refresh замокан
            pass
    apply.assert_called_once_with(mock_client, POST_ID, 'aliceai', 'r1', 0, 7, ANY)


def test_apply_endpoint_payload():
    from itd.api.portal import apply_corrector

    client = MagicMock()
    apply_corrector.__wrapped__(client, POST_ID, 'aliceai', 'r1', 0, 7)
    payload = client.request.call_args.args[2]
    assert payload['operationId'] and payload['revision'] == 'r1' and payload['postId'] == POST_ID
