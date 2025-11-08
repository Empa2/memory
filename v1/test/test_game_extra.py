import json
import os
import time
import re
import pytest
from pathlib import Path

from game import Game, Board, DataLoader, StateError, InvalidMove


# GJORD AV GENERATIV - AI


# -----------------------
# Helpers / Fixtures
# -----------------------

@pytest.fixture
def fake_words():
    # Tillräckligt många ord för hard (8x8 => 32 par)
    # Skapar w1..w80 för marginal
    return [f"w{i}" for i in range(1, 81)]

@pytest.fixture
def patched_words(monkeypatch, fake_words):
    # Mocka DataLoader.load_words globalt
    monkeypatch.setattr(DataLoader, "load_words", lambda self, filename="memo.txt": list(fake_words))

@pytest.fixture
def game(patched_words):
    return Game(seed=1234)

@pytest.fixture
def game_same_seed_A(patched_words):
    return Game(seed=42)

@pytest.fixture
def game_same_seed_B(patched_words):
    return Game(seed=42)

@pytest.fixture
def game_other_seed(patched_words):
    return Game(seed=99)


# -----------------------
# Seed & setup
# -----------------------

def test_same_seed_produces_same_board(game_same_seed_A, game_same_seed_B):
    game_same_seed_A.start_new_game("easy")  # 4x4 => 8 par
    game_same_seed_B.start_new_game("easy")
    # Jämför hela boardens values
    vals_A = [[c["value"] for c in row] for row in game_same_seed_A.board.board]
    vals_B = [[c["value"] for c in row] for row in game_same_seed_B.board.board]
    assert vals_A == vals_B, "Samma seed borde ge identiskt bräde."

def test_different_seed_produces_different_board(game_same_seed_A, game_other_seed):
    game_same_seed_A.start_new_game("easy")
    game_other_seed.start_new_game("easy")
    vals_A = [[c["value"] for c in row] for row in game_same_seed_A.board.board]
    vals_C = [[c["value"] for c in row] for row in game_other_seed.board.board]
    # Kan i princip råka bli lika, men med stor ordlista och shuffle är det extremt osannolikt
    assert vals_A != vals_C, "Olika seed bör normalt ge olika bräde."


# -----------------------
# Position & parsing
# -----------------------

@pytest.mark.parametrize("coord, expected", [
    ("A1", (0, 0)),
    ("a1", (0, 0)),
    ("  b2 ", (1, 1)),
    ("D4", (3, 3)),
])
def test_parse_position_variants(coord, expected):
    b = Board(size=4, word_len=3)
    # skapa ett tomt bräde så get/set funkar om vi använder dem
    b.create_board(["x"]*(4*4))
    assert b.parse_position(coord) == expected

@pytest.mark.parametrize("bad", ["", "A", "11", "Z1", "A0", "A-1", "Ä1", "1A", "AA"])
def test_parse_position_invalid(bad):
    b = Board(size=4, word_len=3)
    b.create_board(["x"]*(4*4))
    with pytest.raises(ValueError):
        b.parse_position(bad)


# -----------------------
# State machine & moves
# -----------------------

def first_two_coords():
    # Hjälpkoordinater: A1 och B1
    return "A1", "B1"

def test_flip_hidden_then_flip_same_raises(game):
    game.start_new_game("easy")
    a1, _ = first_two_coords()
    game.choose_card(a1)
    with pytest.raises(InvalidMove):
        game.choose_card(a1)

def test_cannot_flip_matched(game):
    game.start_new_game("easy")
    a1, b1 = first_two_coords()
    # Tvinga match på A1/B1
    r1, c1 = game.board.parse_position(a1)
    r2, c2 = game.board.parse_position(b1)
    v = "PAIR"
    game.board.board[r1][c1]["value"] = v
    game.board.board[r2][c2]["value"] = v

    # flip → match → försök flip igen
    game.choose_card(a1)
    game.choose_card(b1)
    assert game.match(a1, b1) is True
    with pytest.raises(StateError):
        game.board.set_state(r1, c1, "flipped")
    with pytest.raises(StateError):
        game.board.set_state(r2, c2, "flipped")

def test_mismatch_flips_back_to_hidden(game):
    game.start_new_game("easy")
    a1, b1 = first_two_coords()
    r1, c1 = game.board.parse_position(a1)
    r2, c2 = game.board.parse_position(b1)
    game.board.board[r1][c1]["value"] = "X"
    game.board.board[r2][c2]["value"] = "Y"

    game.choose_card(a1)
    game.choose_card(b1)
    res = game.match(a1, b1)
    assert res is False
    assert game.board.get_state(r1, c1) == "hidden"
    assert game.board.get_state(r2, c2) == "hidden"
    assert game.moves == 1
    assert game.matched_pairs == 0

def test_match_increments_counters_and_sets_end_time_on_last_pair(game):
    game.start_new_game("easy")  # 4x4 => 8 par
    # Vi fyller brädet deterministiskt med fyra par vi kan styra
    # Hämta alla koordinater radvis
    coords = []
    for rr in range(game.board.size):
        for cc in range(game.board.size):
            coords.append((rr, cc))

    # Sätt alla värden i par
    pair_values = [f"P{i}" for i in range(8)]
    deck = []
    for v in pair_values:
        deck.extend([v, v])
    # lägg in deck i board i ordning
    k = 0
    for rr in range(game.board.size):
        for cc in range(game.board.size):
            game.board.board[rr][cc]["value"] = deck[k]
            k += 1

    # Matcha alla par i ordning: (0,1), (2,3), ...
    def coord_of(idx):
        rr, cc = coords[idx]
        col = chr(ord('A') + cc)
        row = rr + 1
        return f"{col}{row}"

    total_pairs = (game.board.size**2)//2
    for i in range(total_pairs - 1):
        c1 = coord_of(2*i)
        c2 = coord_of(2*i + 1)
        game.choose_card(c1)
        game.choose_card(c2)
        assert game.match(c1, c2) is True
        assert game.matched_pairs == i + 1
        assert game.end_time is None  # inte sista än

    # sista paret
    last_c1 = coord_of(2*(total_pairs-1))
    last_c2 = coord_of(2*(total_pairs-1) + 1)
    game.choose_card(last_c1)
    game.choose_card(last_c2)
    before = time.time()
    assert game.match(last_c1, last_c2) is True
    assert game.is_finished() is True
    assert game.end_time is not None
    assert game.end_time >= game.start_time
    assert game.end_time <= before + 1  # rimlig gräns

def test_time_elapsed_freezes_after_finish(game):
    game.start_new_game("easy")
    # skapa ett säkert match-par
    a1, b1 = first_two_coords()
    r1, c1 = game.board.parse_position(a1)
    r2, c2 = game.board.parse_position(b1)
    game.board.board[r1][c1]["value"] = "Z"
    game.board.board[r2][c2]["value"] = "Z"

    t0 = game.time_elapsed()
    time.sleep(0.05)
    game.choose_card(a1)
    game.choose_card(b1)
    game.match(a1, b1)
    t1 = game.time_elapsed()
    # Om spelet inte är klart än kan end_time vara None (bara 1/8 par klara).
    # Forcera klart spel för att testa "freeze":
    game.matched_pairs = (game.board.size**2)//2
    game.end_time = time.time()
    frozen = game.time_elapsed()
    time.sleep(0.05)
    assert game.time_elapsed() == pytest.approx(frozen, rel=0, abs=0.02), "Efter end_time ska tiden vara fryst."


# -----------------------
# Match edge cases
# -----------------------

def test_match_same_coordinate_raises(game):
    game.start_new_game("easy")
    # Samma ruta två gånger → i din implementering leder det till StateError
    # eftersom andra set_state("matched") träffar redan matched cell.
    with pytest.raises(StateError):
        # För att undvika InvalidMove (flippa först)
        game.choose_card("A1")
        # sätt ett värde så matchvillkoret triggas på samma cell (value==value)
        r, c = game.board.parse_position("A1")
        v = game.board.get_value(r, c)
        # Skicka samma koordinat två gånger
        game.match("A1", "A1")


def test_board_str_has_header_and_rows(game):
    b = Board(size=4, word_len=3)
    b.create_board(["abc"]*(4*4))
    s = str(b)
    # En enkel sanity-koll: har header med A B C D och radnummer
    assert re.search(r"A\s+B\s+C\s+D", s), s
    assert "| " in s
    assert " 1 " in s or " 1|" in s


# -----------------------
# DataLoader behavior
# -----------------------

def test_pick_words_not_enough(monkeypatch):
    dl = DataLoader(base_path=Path.cwd() / "tmp_data1")
    monkeypatch.setattr(DataLoader, "load_words", lambda self, filename="memo.txt": ["a", "b", "c"])
    with pytest.raises(ValueError):
        dl.pick_words(5)

def test_load_save_score_roundtrip(tmp_path):
    # Använd separat datakatalog
    dl = DataLoader(base_path=tmp_path)
    # Bör vara tom från början
    assert dl.load_score() == []
    # Spara två resultat
    dl.save_score({"name": "A", "time": 10})
    dl.save_score({"name": "B", "time": 8})
    data = dl.load_score()
    assert isinstance(data, list)
    assert data[-2:] == [{"name": "A", "time": 10}, {"name": "B", "time": 8}]

def test_load_score_invalid_json_returns_empty(tmp_path):
    dl = DataLoader(base_path=tmp_path)
    # Skriv trasig JSON
    score_file = dl.score_path / "score.json"
    score_file.write_text("{not json", encoding="utf-8")
    data = dl.load_score()
    assert data == [], "Trasig JSON ska resultera i tom lista, inte krasch."

def test_save_score_is_atomic(tmp_path):
    dl = DataLoader(base_path=tmp_path)
    # Kör save_score – ska skriva via .tmp och sedan ersätta
    dl.save_score({"n": 1})
    # Kolla att score.json finns och inte .tmp
    assert (dl.score_path / "score.json").exists()
    assert not (dl.score_path / "score.tmp").exists()
