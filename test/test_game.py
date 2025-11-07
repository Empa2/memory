import pytest
from game import Game, Board, DataLoader, StateError, InvalidMove
from pathlib import Path
import time


# GJORD AV GENERATIV - AI


@pytest.fixture
def game():
    return Game(seed=42)

@pytest.fixture 
def board():
    return Board(4, 5)

def test_game_init(game):
    assert game.seed == 42
    assert game.board is None
    assert game.moves == 0
    assert game.matched_pairs == 0
    assert game.start_time is None
    assert game.end_time is None
    assert game.settings == {"easy": 4, "medium": 6, "hard": 8}

def test_start_new_game(game):
    game.start_new_game("easy")
    assert game.board is not None
    assert game.board.size == 4
    assert game.moves == 0
    assert game.matched_pairs == 0
    assert game.start_time is not None
    assert game.end_time is None

def test_invalid_difficulty(game):
    with pytest.raises(ValueError):
        game.start_new_game("invalid")

def test_choose_card(game):
    game.start_new_game("easy")
    row, col = game.choose_card("A1")
    assert row == 0
    assert col == 0
    assert game.board.get_state(row, col) == "flipped"

def test_choose_card_no_game(game):
    with pytest.raises(InvalidMove):
        game.choose_card("A1")

def test_choose_flipped_card(game):
    game.start_new_game("easy")
    game.choose_card("A1")
    with pytest.raises(InvalidMove):
        game.choose_card("A1")

def test_match_cards(game):
    game.start_new_game("easy")
    # Mock matching cards
    game.board.board[0][0]["value"] = "test"
    game.board.board[0][1]["value"] = "test"
    game.choose_card("A1")
    game.choose_card("B1")
    assert game.match("A1", "B1") == True
    assert game.moves == 1
    assert game.matched_pairs == 1

def test_no_match_cards(game):
    game.start_new_game("easy")
    game.board.board[0][0]["value"] = "test1"
    game.board.board[0][1]["value"] = "test2"
    game.choose_card("A1")
    game.choose_card("B1")
    assert game.match("A1", "B1") == False
    assert game.moves == 1
    assert game.matched_pairs == 0

def test_board_parse_position(board):
    row, col = board.parse_position("A1")
    assert row == 0
    assert col == 0
    
    with pytest.raises(ValueError):
        board.parse_position("A")
    with pytest.raises(ValueError):
        board.parse_position("11")
    with pytest.raises(ValueError):
        board.parse_position("Z1")

def test_board_set_state(board):
    board.create_board(["test"]*16)
    board.set_state(0, 0, "flipped")
    assert board.get_state(0, 0) == "flipped"
    
    with pytest.raises(StateError):
        board.set_state(0, 0, "flipped")

def test_time_elapsed(game):
    assert game.time_elapsed() == 0
    game.start_new_game("easy")
    time.sleep(0.1)
    assert game.time_elapsed() > 0

def test_is_finished(game):
    game.start_new_game("easy")
    assert game.is_finished() == False
    game.matched_pairs = 8
    assert game.is_finished() == True