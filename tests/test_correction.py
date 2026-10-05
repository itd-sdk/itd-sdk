from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from itd.core.default import set_default_client

from itd.enums import NotebookStyle
from itd.models.correction import CorrectorState, RedPenState, apply_marks, visible_marks
from itd.models.post import Post

pytestmark = pytest.mark.usefixtures('keep_default_client')


def iso(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) + delta).isoformat().replace('+00:00', 'Z')


ACTOR = {'id': '00000000-0000-0000-0000-000000000099', 'username': 'dezhurny', 'displayName': 'Дежурный'}
TEXT = 'Сегодня мы пошли в школу 😀 Вообще ничего не понятно'

CORRECTOR = {
    'revision': 'r1',
    'serverTime': iso(timedelta()),
    'events': [{'id': 'aliceai', 'endsAt': iso(timedelta(days=1)), 'applicationsEnabled': True}],
    'marks': [
        {'id': 'm1', 'start': 11, 'end': 16, 'eventId': 'aliceai', 'actor': ACTOR, 'endsAt': iso(timedelta(hours=1))},
        {'id': 'm2', 'start': 0, 'end': 7, 'eventId': 'aliceai', 'actor': ACTOR, 'endsAt': iso(-timedelta(hours=1))},  # истекла
    ],
}
RED_PEN = {
    'revision': 'r1',
    'events': [{'id': 'aliceai', 'endsAt': iso(timedelta(days=1))}],
    'claim': {'id': 'c1', 'eventId': 'aliceai', 'actor': ACTOR, 'isOwner': True, 'endsAt': iso(timedelta(hours=1))},
    # после эмодзи (2 единицы UTF-16) смещения сдвигаются
    'corrections': [{'id': 'p1', 'start': 28, 'end': 34, 'replacement': 'Ваще'}],
}
POST_DATA = {
    'id': '00000000-0000-0000-0000-000000000001',
    'author': {'id': '00000000-0000-0000-0000-000000000002', 'username': 'author', 'displayName': 'Автор', 'avatar': '😀'},
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
    set_default_client(client)  # Comments() поста создается без клиента и берет дефолтный
    return client


@pytest.fixture
def post(mock_client):
    return Post.from_dict(POST_DATA, client=mock_client)


def test_post_fields(post):
    assert post.notebook is not None and post.notebook.style == NotebookStyle.RULED
    assert post.corrector is not None and len(post.corrector.marks) == 2
    assert post.red_pen is not None and post.red_pen.corrections[0].replacement == 'Ваще'


def test_post_without_tools(mock_client):
    mock_client.config.load_on_getattr = False  # иначе отсутствующее поле перезагрузит пост из апи
    data = {k: v for k, v in POST_DATA.items() if k not in ('notebook', 'corrector', 'redPen')}
    post = Post.from_dict(data, client=mock_client)
    assert post.notebook is None and post.corrector is None and post.red_pen is None
    assert post.masked_content == TEXT


def test_active_marks():
    state = CorrectorState.model_validate(CORRECTOR)
    assert [mark.id for mark in state.active_marks] == ['m1']
    assert str(state.marks[0].actor) == '@dezhurny'
    assert state.active_event is not None and state.active_event.id == 'aliceai'


def test_single_claim_to_list():
    state = RedPenState.model_validate(RED_PEN)
    assert len(state.claims) == 1
    assert state.own_claim is not None and state.own_claim.id == 'c1'
    assert len(state.active_corrections) == 1


def test_expired_claim_hides_corrections():
    state = RedPenState.model_validate({**RED_PEN, 'claim': {**RED_PEN['claim'], 'endsAt': iso(-timedelta(minutes=1))}})
    assert state.active_corrections == []


def test_masked_content(post):
    # правка красной ручкой в текст не подставляется, только замазка
    assert post.masked_content == 'Сегодня мы ■■■■■ в школу 😀 Вообще ничего не понятно'


def test_newer_red_pen_hides_mark():
    corrector = CorrectorState.model_validate(
        {
            'marks': [
                {'id': 'm1', 'start': 0, 'end': 7, 'createdAt': '2026-09-01T00:00:00Z'},
                {'id': 'm2', 'start': 8, 'end': 10, 'createdAt': '2026-09-03T00:00:00Z'},
            ]
        }
    )
    red_pen = RedPenState.model_validate(
        {
            'corrections': [
                {'id': 'p1', 'start': 0, 'end': 7, 'replacement': 'Завтра', 'createdAt': '2026-09-02T00:00:00Z'},  # позже m1
                {'id': 'p2', 'start': 8, 'end': 10, 'replacement': 'вы', 'createdAt': '2026-09-02T00:00:00Z'},  # раньше m2
            ]
        }
    )
    assert [mark.id for mark in visible_marks(corrector.marks, red_pen.corrections)] == ['m2']


def test_apply_marks():
    corrector = CorrectorState.model_validate({'marks': [{'id': 'm', 'start': 0, 'end': 7}, {'id': 'n', 'start': 5, 'end': 13}]})
    assert apply_marks(TEXT, corrector.marks) == '■■■■■■■ ■■ ■■шли в школу 😀 Вообще ничего не понятно'  # пересечение не ломает текст
    assert apply_marks('a b', []) == 'a b'


def test_apply_corrector_calls_api(post, mock_client):
    with patch('itd.models.post.apply_corrector') as apply, patch('itd.models.post.Post.refresh_corrections') as refresh:
        post.apply_corrector(0, 7)
    apply.assert_called_once_with(mock_client, post.id, 'aliceai', 'r1', 0, 7)
    refresh.assert_called_once()


def test_cancel_red_pen_uses_own_claim(post, mock_client):
    with patch('itd.models.post.cancel_red_pen') as cancel, patch('itd.models.post.Post.refresh_corrections'):
        post.cancel_red_pen()
    cancel.assert_called_once_with(mock_client, post.id, 'c1')


def test_apply_without_event(mock_client):
    post = Post.from_dict({**POST_DATA, 'corrector': {'marks': []}}, client=mock_client)
    with pytest.raises(ValueError, match='no active event'):
        post.apply_corrector(0, 1)
