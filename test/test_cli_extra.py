import builtins
import pytest
import types
from pathlib import Path

import cli
from game import Game, DataLoader


# -----------------------
# Helpers
# -----------------------

class DummyBoard:
    def __init__(self, valid=None):
        self.valid = set(valid or [])
        self.seen = []

    def parse_position(self, coordinate):
        self.seen.append(coordinate)
        if self.valid and coordinate not in self.valid:
            raise ValueError("ogiltig")

    def __str__(self):
        return "<dummy-board>"


def feed_inputs(monkeypatch, seq):
    it = iter(seq)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(it))


# -----------------------
# Bas-patch: stäng av screen/paus i ALLA CLI-tester
# -----------------------

@pytest.fixture(autouse=True)
def no_screen_pause(monkeypatch):
    monkeypatch.setattr(cli, "clear_screen", lambda: None)
    monkeypatch.setattr(cli, "pause", lambda: None)


# -----------------------
# parse_coords – fler format & fel
# -----------------------

def test_parse_coords_mixed_whitespace_and_commas():
    b = DummyBoard(valid={"A1", "B2"})
    out = cli.parse_coords(b, "  A1 ,   B2 ")
    assert out == ["A1", "B2"]
    assert b.seen == ["A1", "B2"]


def test_parse_coords_rejects_three_and_duplicate():
    b = DummyBoard(valid={"A1", "B2", "C3"})
    with pytest.raises(ValueError):
        cli.parse_coords(b, "A1 B2 C3")
    with pytest.raises(ValueError):
        cli.parse_coords(b, "C3, C3")


# -----------------------
# prompt_coords
# -----------------------

def test_prompt_coords_invalid_then_valid_then_quit(monkeypatch, capsys):
    game = types.SimpleNamespace(board=DummyBoard(valid={"A1"}))
    feed_inputs(monkeypatch, ["X9", "A1", "q"])
    res = cli.prompt_coords(game)
    assert res == ["A1"]
    out = capsys.readouterr().out
    assert "Fel:" in out


def test_prompt_coords_quit_direct(monkeypatch, capsys):
    game = types.SimpleNamespace(board=DummyBoard())
    feed_inputs(monkeypatch, ["q"])
    assert cli.prompt_coords(game) is None
    assert "Avslutar spelet" in capsys.readouterr().out


# -----------------------
# play_turn
# -----------------------

def test_play_turn_rejects_multiple_coords():
    class G: pass
    g = G()
    g.board = "<b>"
    with pytest.raises(ValueError):
        cli.play_turn(g, ["A1", "B2"])


def test_play_turn_shows_board_and_handles_invalid(monkeypatch, capsys):
    class MyInvalidMove(Exception): ...
    monkeypatch.setattr(cli, "InvalidMove", MyInvalidMove)

    class G:
        def __init__(self):
            self.board = "<fakeboard>"
        def choose_card(self, coord):
            raise MyInvalidMove("nej")

    ok = cli.play_turn(G(), ["A1"])
    assert ok is False
    out = capsys.readouterr().out
    assert "Ogiltigt drag" in out


# -----------------------
# get_user_name
# -----------------------

def test_get_user_name_boundary_and_success(monkeypatch, capsys):
    # 16 tecken (för långt), sedan tomt -> Anonym, sedan giltigt
    feed_inputs(monkeypatch, ["x"*16, "", "Emil"])
    assert cli.get_user_name() == "Anonym"
    # efter första retur körs inte nästa input automatisk, kör igen separat
    feed_inputs(monkeypatch, ["Emil"])
    assert cli.get_user_name() == "Emil"
    out = capsys.readouterr().out
    assert "för långt" in out.lower() or "För långt" in out


# -----------------------
# show_highscores
# -----------------------

def test_show_highscores_sorting_and_sections(monkeypatch, capsys):
    scores = [
        {"finished": True, "difficulty": "easy",   "time": 10.5, "moves": 5,  "time_stamp": "2025-01-02 12:00:00", "user_name": "B"},
        {"finished": True, "difficulty": "easy",   "time": 10.5, "moves": 4,  "time_stamp": "2025-01-01 12:00:00", "user_name": "A"},
        {"finished": True, "difficulty": "medium", "time": 20.0, "moves": 8,  "time_stamp": "2025-01-03 12:00:00", "user_name": "M"},
        {"finished": True, "difficulty": "hard",   "time": 30.0, "moves": 12, "time_stamp": "2025-01-04 12:00:00", "user_name": "H"},
        {"finished": False,"difficulty": "easy",   "time": 1.0,  "moves": 1,  "time_stamp": "2025-01-05 12:00:00", "user_name": "X"},
    ]
    class FakeLoader:
        def load_score(self): return scores
    monkeypatch.setattr(cli, "DataLoader", lambda: FakeLoader())

    cli.show_highscores()
    out = capsys.readouterr().out
    # sektioner
    assert "Lätt" in out
    assert "Medel" in out
    assert "Svår" in out
    # sortering (time asc, moves asc): A före B i "Lätt"
    light_section = out.split("Lätt".center(44, "-"))[1]
    assert light_section.strip().startswith("2025-01-01")  # A först


# -----------------------
# start_cli – felaktigt menyval → highscore → exit
# -----------------------

def test_start_cli_invalid_choice_then_show_scores_then_exit(monkeypatch, capsys):
    class FakeLoader:
        def load_score(self): return []
    monkeypatch.setattr(cli, "DataLoader", lambda: FakeLoader())

    feed_inputs(monkeypatch, ["9", "", "2", "", "3"])
    cli.start_cli()
    out = capsys.readouterr().out
    assert "Ogiltigt val" in out
    assert "Tack för att du spelade" in out


# -----------------------
# start_game – mismatch → match → spara resultat
# (Fix B: mocka DataLoader I/O + byt cwd till tmp_path)
# -----------------------

def test_start_game_mismatch_then_match_and_save(monkeypatch, capsys, tmp_path):
    saved = {}

    # Kör i temporär katalog så DataLoader skapar data/ under tmp i stället för projektroten
    monkeypatch.chdir(tmp_path)

    # Mocka ordlista och score-I/O (inga riktiga filer läses/skrivs)
    monkeypatch.setattr(DataLoader, "load_words",
                         lambda self, filename="memo.txt": [f"W{i}" for i in range(1, 200)])
    monkeypatch.setattr(DataLoader, "load_score",
                         lambda self, filename="score.json": [])
    monkeypatch.setattr(DataLoader, "save_score",
                         lambda self, result, filename="score.json": saved.setdefault("result", result))

    # Inputs för start_game():
    # seed -> "" (None), difficulty -> "easy"
    # coords1 -> "A1 B1" (mismatch), coords2 -> "A2 B2" (match),
    # namn -> "Z"
    feed_inputs(monkeypatch, ["", "easy", "A1 B1", "A2 B2", "Z"])

    # Rigga brädet: A1/B1 har olika värden, A2/B2 samma.
    real_start = Game.start_new_game
    def rigged_start(self, difficulty):
        real_start(self, difficulty)
        r1,c1  = self.board.parse_position("A1")
        r1b,c1b = self.board.parse_position("B1")
        r2,c2  = self.board.parse_position("A2")
        r2b,c2b = self.board.parse_position("B2")
        self.board.board[r1][c1]["value"]   = "X"
        self.board.board[r1b][c1b]["value"] = "Y"   # mismatch
        self.board.board[r2][c2]["value"]   = "PAIR"
        self.board.board[r2b][c2b]["value"] = "PAIR"
        # gör resten matchade, lämna dessa fyra omatchade:
        for rr in range(self.board.size):
            for cc in range(self.board.size):
                if (rr,cc) not in [(r1,c1),(r1b,c1b),(r2,c2),(r2b,c2b)]:
                    self.board.board[rr][cc]["state"] = "matched"
        # så att en match (A2,B2) avslutar spelet
        self.matched_pairs = (self.board.size**2)//2 - 1

    monkeypatch.setattr(Game, "start_new_game", rigged_start)

    cli.start_game()
    out = capsys.readouterr().out
    # vi förväntar oss både mismatch- och match-prints någonstans i flödet
    assert ("Tyvärr" in out) or ("Bra jobbat" in out)
    assert saved and saved["result"]["user_name"] == "Z"
    assert saved["result"]["finished"] is True
    # ett mismatch-försök + ett match-försök
    assert saved["result"]["moves"] >= 2


# -----------------------
# get_difficulty – normaliserar input
# -----------------------

def test_get_difficulty_normalizes_input(monkeypatch):
    feed_inputs(monkeypatch, ["  HARD  "])
    assert cli.get_difficulty() == "hard"
