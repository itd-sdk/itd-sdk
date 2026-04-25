from unittest.mock import patch, MagicMock
from uuid import UUID

import pytest

from itd.poll import Poll, NewPoll


POLL_DATA = {
    'id': '00000000-0000-0000-0000-000000000001',
    'postId': '00000000-0000-0000-0000-000000000002',
    'createdAt': '2024-12-01T00:00:00Z', # итд 2024 кста
    'question': 'Лучший язык?',
    'options': [
        {'id': '00000000-0000-0000-0000-000000000010', 'text': 'Python', 'votesCount': 5},
        {'id': '00000000-0000-0000-0000-000000000011', 'text': 'Rust', 'votesCount': 3},
    ],
    'multipleChoice': False,
    'hasVoted': False,
    'votedOptionIds': [],
    'totalVotes': 8,
}

PYTHON_ID = UUID('00000000-0000-0000-0000-000000000010')
RUST_ID = UUID('00000000-0000-0000-0000-000000000011')


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.token = 'mock_token'
    return client


@pytest.fixture
def poll(mock_client):
    return Poll(POLL_DATA, mock_client)


def test_poll_str(poll):
    assert str(poll) == 'Лучший язык?'


def test_poll_int(poll):
    assert int(poll) == 8


def test_poll_bool_not_voted(poll):
    assert not bool(poll)


def test_poll_options_count(poll):
    assert len(poll.options) == 2


def test_poll_option_str(poll):
    assert str(poll.options[0]) == 'Python'
    assert str(poll.options[1]) == 'Rust'


def test_poll_option_int(poll):
    assert int(poll.options[0]) == 5
    assert int(poll.options[1]) == 3


def test_poll_vote_invalid_text(poll):
    with pytest.raises(ValueError, match='not found'):
        poll.vote('Go')


def test_poll_vote_invalid_type(poll):
    with pytest.raises(TypeError):
        poll.vote(123)


def test_poll_vote_invalid_type_in_list(poll):
    with pytest.raises(TypeError):
        poll.vote([123])


def test_poll_vote_invalid_text_in_list(poll):
    with pytest.raises(ValueError, match='not found'):
        poll.vote(['Go'])


@patch('itd.poll.vote')
def test_poll_vote_by_text(mock_vote, poll):
    poll.vote('Python')
    mock_vote.assert_called_once()
    _, _, option_ids = mock_vote.call_args[0]
    assert PYTHON_ID in option_ids


@patch('itd.poll.vote')
def test_poll_vote_by_uuid(mock_vote, poll):
    poll.vote(RUST_ID)
    mock_vote.assert_called_once()
    _, _, option_ids = mock_vote.call_args[0]
    assert RUST_ID in option_ids


@patch('itd.poll.vote')
def test_poll_vote_by_option_object(mock_vote, poll):
    poll.vote(poll.options[0])
    mock_vote.assert_called_once()
    _, _, option_ids = mock_vote.call_args[0]
    assert PYTHON_ID in option_ids


@patch('itd.poll.vote')
def test_poll_vote_list_of_text(mock_vote, poll):
    poll.vote(['Python', 'Rust'])
    mock_vote.assert_called_once()
    _, _, option_ids = mock_vote.call_args[0]
    assert len(option_ids) == 2
    assert PYTHON_ID in option_ids
    assert RUST_ID in option_ids


@patch('itd.poll.vote')
def test_poll_vote_list_of_uuids(mock_vote, poll):
    poll.vote([PYTHON_ID, RUST_ID])
    _, _, option_ids = mock_vote.call_args[0]
    assert PYTHON_ID in option_ids
    assert RUST_ID in option_ids


def test_new_poll_from_poll(poll):
    new = NewPoll.from_poll(poll)
    assert new.poll.question == poll.question
    assert len(new.poll.options) == len(poll.options)
    assert new.poll.options[0].text == str(poll.options[0])
    assert new.poll.options[1].text == str(poll.options[1])
