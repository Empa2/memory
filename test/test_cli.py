import builtins
import types
import pytest
import cli

class DummyBoard:
    def __init__(self, valid_coords=None):
        self.valid_coords = set(valid_coords or [])
        self.parsed = []

    def parse_position(self, coordinate):
        self.parsed.append(coordinate)
        if self.valid_coords and coordinate not in self.valid_coords:
            raise ValueError(f"Ogiltig ruta: {coordinate}")

    def __str__(self):
        return "<board>"


def test_parse_coords_single_and_pair():
    board = DummyBoard(valid_coords={"A1", "B2"})
    res = cli.parse_coords(board, "A1")
    assert res == ["A1"]
    res = cli.parse_coords(board, "A1 B2")
    assert res == ["A1", "B2"]
    res = cli.parse_coords(board, "A1,B2")
    assert res == ["A1", "B2"]
    assert board.parsed == ["A1", "A1", "B2", "A1", "B2"]  # called for each parse


def test_parse_coords_empty_and_too_many_and_duplicate():
    board = DummyBoard(valid_coords={"A1", "B2", "C3"})
    with pytest.raises(ValueError):
        cli.parse_coords(board, "")
    with pytest.raises(ValueError):
        cli.parse_coords(board, "A1 B2 C3")
    with pytest.raises(ValueError):
        cli.parse_coords(board, "A1 A1")


def test_parse_coords_propagates_board_errors():
    board = DummyBoard(valid_coords={"A1"})
    with pytest.raises(ValueError) as exc:
        cli.parse_coords(board, "Z9")
    assert "Ogiltig ruta" in str(exc.value) or "Z9" in str(exc.value)


def test_play_turn_success(monkeypatch, capsys):
    # avoid clearing the real terminal
    monkeypatch.setattr(cli, "clear_screen", lambda: None)
    class FakeGame:
        def __init__(self):
            self.board = "<fakeboard>"
            self.chosen = None
        def choose_card(self, coord):
            self.chosen = coord
    game = FakeGame()
    ok = cli.play_turn(game, ["A1"])
    assert ok is True
    assert game.chosen == "A1"
    captured = capsys.readouterr()
    # game.board printed
    assert "<fakeboard>" in captured.out


def test_play_turn_invalid_move(monkeypatch, capsys):
    monkeypatch.setattr(cli, "clear_screen", lambda: None)
    class MyInvalidMove(Exception):
        pass
    # replace cli.InvalidMove to our class for raising
    monkeypatch.setattr(cli, "InvalidMove", MyInvalidMove)
    class FakeGame:
        def __init__(self):
            self.board = "<fakeboard>"
        def choose_card(self, coord):
            raise MyInvalidMove("not allowed")
    game = FakeGame()
    ok = cli.play_turn(game, ["A1"])
    assert ok is False
    out = capsys.readouterr().out
    assert "Ogiltigt drag" in out or "not allowed" in out


def test_get_difficulty_accepts_after_invalid(monkeypatch):
    inputs = iter(["bad", "MEDIUM"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    v = cli.get_difficulty()
    assert v == "medium"


def test_get_seed_empty_and_nonempty(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")
    assert cli.get_seed() is None
    monkeypatch.setattr(builtins, "input", lambda prompt="": "  s123  ")
    assert cli.get_seed() == "s123"


def test_get_user_name_long_then_anonymous(monkeypatch, capsys):
    inputs = iter(["thisnameiswaytoolongtobeaccepted", ""])
    def fake_input(prompt=""):
        return next(inputs)
    monkeypatch.setattr(builtins, "input", fake_input)
    name = cli.get_user_name()
    assert name == "Anonym"
    # ensure warning printed on too long name
    # call again with a valid short name
    inputs = iter(["validname"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    assert cli.get_user_name() == "validname"


def test_show_highscores_outputs_sections(monkeypatch, capsys):
    # Prepare fake scores
    scores = [
        {"finished": True, "difficulty": "easy", "time": 10.5, "moves": 5, "time_stamp": "2025-01-01 12:00:00", "user_name": "Alice"},
        {"finished": True, "difficulty": "medium", "time": 20.0, "moves": 8, "time_stamp": "2025-01-02 12:00:00", "user_name": "Bob"},
        {"finished": True, "difficulty": "hard", "time": 30.0, "moves": 12, "time_stamp": "2025-01-03 12:00:00", "user_name": "Carol"},
        {"finished": False, "difficulty": "easy", "time": 5.0, "moves": 2, "time_stamp": "2025-01-04 12:00:00", "user_name": "IgnoreMe"},
    ]
    class FakeLoader:
        def load_score(self):
            return scores
    monkeypatch.setattr(cli, "DataLoader", lambda: FakeLoader())
    cli.show_highscores()
    out = capsys.readouterr().out
    assert "Lätt" in out or "Lätt" in out  # section header in Swedish
    assert "Medel" in out
    assert "Svår" in out
    assert "Alice" in out and "Bob" in out and "Carol" in out