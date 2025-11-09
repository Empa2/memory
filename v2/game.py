from enum import Enum, auto
import string
import time
import random
from pathlib import Path
import json


DIFFICULTIES = {
    "easy": 4,
    "medium":6,
    "hard": 8,
}
ALLOWED_DIFFICULTIES = set(DIFFICULTIES.keys())

REQUIRED_SCORE_FIELDS = {
    "game_id",
    "user_name",
    "moves",
    "time",
    "difficulty",
    "finished",
    "timestamp",
    "seed",
}


class CardState(Enum):
    HIDDEN = auto()
    FLIPPED = auto()
    MATCHED = auto()


class GameState(Enum):
    WAIT_FIRST = auto()
    WAIT_SECOND = auto()
    RESOLVING = auto()
    FINISHED = auto()


class GameError(Exception):
    pass

class InvalidMove(GameError):
    pass

class CoordinateError(GameError):
    pass

class GameStateError(GameError):
    pass


class Card:
    def __init__(self, value):
        self.value = value
        self.state = CardState.HIDDEN

    def set_state(self, new_state):
        if self.state == CardState.MATCHED and new_state != CardState.MATCHED:
            raise GameStateError("Kan inte ändra state på ett matchat kort.")

        self.state = new_state

    def __repr__(self):
        return f"Card(value={self.value!r}, state={self.state.name})"

class Board:
    def __init__(self, size):
        self.size = size
        self.board = []

    def create_board(self, deck):
        values = list(deck)
        expected = self.size * self.size
        if len(values) != expected:
            raise GameError(f"Fel antal kort: fick {len(values)}, förväntade {expected}")
        it = iter(values)
        board = []
        for _ in range(self.size):
            row = []
            for _ in range(self.size):
                value = next(it)
                row.append(Card(value))
            board.append(row)
        self.board = board

    def get_card(self, row, col):
        if not self.in_bounds(row, col):
            raise CoordinateError("Position utanför brädet.")
        return self.board[row][col]

    def in_bounds(self, row, col):
        return 0 <= row < self.size and 0 <=col < self.size

    def iter_cards(self):
        for row in self.board:
            for card in row:
                yield card

    def all_cards(self):
        return list(self.iter_cards())

    def iter_positions(self):
        for row in range(self.size):
            for col in range(self.size):
                yield row, col

    def hidden_positions(self):
        return [(row, col) for (row, col) in self.iter_positions() if self.board[row][col].state == CardState.HIDDEN]

    def flipped_positions(self):
        return [(row, col) for (row, col) in self.iter_positions() if self.board[row][col].state == CardState.FLIPPED]

    def matched_positions(self):
        return [(row, col) for (row, col) in self.iter_positions() if self.board[row][col].state == CardState.MATCHED]

    def reset_flipped(self):
        for row in range(self.size):
            for col in range(self.size):
                card = self.board[row][col]
                if card.state == CardState.FLIPPED:
                    card.set_state(CardState.HIDDEN)

    def parse_coord(self, coord):
        coord = coord.strip().upper()
        if len(coord) < 2:
            raise CoordinateError("Ange en koordinat, t.ex. A1.")
        col = ord(coord[0]) - ord("A")
        row = int(coord[1:]) - 1

        if not self.in_bounds(row, col):
            raise CoordinateError("Koordinaten ligger utanför brädet.")
        return row, col

    def __str__(self):
        if not self.board:
            return "<tomt bräde>"

        longest = max(len(str(card.value)) for card in self.iter_cards())
        letters = list(string.ascii_uppercase[:self.size])
        header = " "*(longest//2+5) + " ".join(letter.ljust(longest) for letter in letters)
        rows = [header]
        for i, row in enumerate(self.board, start=1):
            row_cells = []
            for card in row:
                if card.state != CardState.HIDDEN:
                    cell_str = str(card.value).ljust(longest)
                else:
                    cell_str = ("-"*longest).ljust(longest)
                row_cells.append(cell_str)
            row_str = " ".join(row_cells)
            rows.append(f"{i:<2} | {row_str}")
        return "\n".join(rows)

class Game:
    def __init__(self, board, difficulty, seed=None, rng=None):
        self.board = board
        self.difficulty = difficulty
        self.seed = seed
        self.rng = rng or random.Random(seed)

        self._state = GameState.WAIT_FIRST
        self._start_ts = None
        self._end_ts = None
        self.moves = 0

    def start_new_game(self, deck):
        local_deck = list(deck)
        self.rng.shuffle(local_deck)
        self.board.create_board(local_deck)

        self._state = GameState.WAIT_FIRST
        self.moves = 0
        self._start_ts = None
        self._end_ts = None

        if self._all_pairs_matched():
            self._state = GameState.FINISHED
            self._end_ts = time.time()

    def state(self):
        return self._state

    def is_finished(self):
        return self._state == GameState.FINISHED

    def time_elapsed(self):
        if self._start_ts is None:
            return 0.0
        if self._end_ts is not None:
            return self._end_ts - self._start_ts
        return time.time() - self._start_ts

    def current_selection(self):
        return self.board.flipped_positions()

    def allowed_moves(self):
        if self._state == GameState.WAIT_FIRST:
            return self.board.hidden_positions()

        if self._state == GameState.WAIT_SECOND:
            return self.board.hidden_positions()

        return []

    def can_flip(self, row, col):
        return (row, col) in self.allowed_moves()

    def flip(self, row, col):
        if self._state not in (GameState.WAIT_FIRST, GameState.WAIT_SECOND):
            raise GameStateError("Kan inte vända kort i detta läge.")

        if not self.board.in_bounds(row, col):
            raise CoordinateError("Positionen ligger utanför brädet.")

        if not self.can_flip(row, col):
            raise InvalidMove("Ogiltigt drag just nu.")

        card = self.board.get_card(row, col)
        if card.state != CardState.HIDDEN:
            raise InvalidMove("Kortet är inte dolt")

        card.set_state(CardState.FLIPPED)
        if self._start_ts is None:
            self._start_ts = time.time()
        flipped = self.board.flipped_positions()

        if len(flipped) == 1:
            self._state = GameState.WAIT_SECOND
        elif len(flipped) == 2:
            self._state = GameState.RESOLVING
        else:
            raise GameError("Internt fel: fler än två kort uppvända")

    def resolve(self):
        if self._state != GameState.RESOLVING:
            raise GameStateError("Kan inte Resolve i detta läge")

        flipped = self.board.flipped_positions()
        if len(flipped) != 2:
            raise GameError("Internt fel: resolve utan två uppvända kort")

        (row1, col1), (row2, col2) = flipped
        card1 = self.board.get_card(row1, col1)
        card2 = self.board.get_card(row2, col2)

        matched = (card1.value == card2.value)

        self.moves += 1

        if matched:
            card1.set_state(CardState.MATCHED)
            card2.set_state(CardState.MATCHED)

        else:
            self.board.reset_flipped()

        if self._all_pairs_matched():
            self._state = GameState.FINISHED
            self._end_ts = time.time()
        else:
            self._state = GameState.WAIT_FIRST

        return {
            "matched": matched,
            "first": (row1, col1),
            "second": (row2, col2),
        }

    def _all_pairs_matched(self):
        return len(self.board.matched_positions()) == self.board.size * self.board.size


class WordRepository:
    def __init__(self, base_path, filename="memo.txt", encoding="utf-8"):
        self.base_path = Path(base_path)
        self.filename = filename
        self.encoding = encoding

        self._words = None

    def load_words(self):
        if self._words is not None:
            return self._words
        path = self.base_path / self.filename
        with path.open("r", encoding=self.encoding) as f:
            loaded_list = [line.strip() for line in f if line.strip()]
            mojibacke = ("Ã¥", "Ã¤", "Ã¶")
            fixed_words = []
            for s in loaded_list:
                if any(marker in s for marker in mojibacke):
                    try:
                        s = s.encode("latin-1").decode("utf-8")
                    except UnicodeError:
                        pass
                fixed_words.append(s)
        self._words = fixed_words
        return self._words

    def pick_words(self, n, rng):
        words = self.load_words()
        if len(words) < n:
            raise ValueError("Inte tillräckligt med ord i ordlistan.")
        return rng.sample(words, n)


class ScoreRepository:
    def __init__(self, base_path, filename="score.json", allowed_difficulties=None, required_fields=None):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.path = self.base_path / filename

        self.allowed_difficulties = set(allowed_difficulties or [])
        self.required_fields = set(required_fields or [])

    def load(self):
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Score filen är korrupt: {self.path}") from e

            if not isinstance(data, list):
                raise ValueError("Score filen måste innehålla en lista")
        return data

    def append(self, entry):
        self._validate_entry(entry)
        data = self.load()
        data.append(entry)

        tmp = self.path.with_suffix(".tmp")

        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.flush()

        tmp.replace(self.path)


    def _validate_entry(self, entry):
        if self.required_fields:
            missing = self.required_fields - set(entry.keys())
            if missing:
                raise ValueError(f"saknar fält i score entry {', '.join(sorted(missing))}")

        if self.allowed_difficulties:
            diff = entry.get("difficulty")
            if diff not in self.allowed_difficulties:
                raise ValueError(f"Ogiltigt difficulty: {diff}")

        moves = entry.get("moves")
        if not isinstance(moves, int) or moves < 0:
            raise ValueError("moves måste vara ett heltal >= 0")

        time_val = entry.get("time")
        if not isinstance(time_val, (int, float)) or time_val <= 0:
            raise ValueError("time måste vara ett tal > 0 sekunder")

        finished = entry.get("finished")
        if not isinstance(finished, bool):
            raise ValueError("finished måste vara True eller False")

    def top(self, difficulty, limit=None):
        if self.allowed_difficulties and difficulty not in self.allowed_difficulties:
            raise ValueError(f"Ogiltig svårighetsgrad: {difficulty}")

        records = [s for s in self.load() if s.get("finished") and s.get("difficulty") == difficulty]
        records.sort(key=lambda x: (x.get("moves", float("inf")), x.get("time", float("inf"))))

        if limit is None:
            return records
        return records[:limit]


def build_deck(word_repo, n_pairs, rng):
    if not isinstance(n_pairs, int) or n_pairs < 1:
        raise ValueError("n_pairs måste vara ett heltal ≥ 1")

    words = word_repo.pick_words(n_pairs, rng)
    deck = [w for w in words for _ in (0, 1)]
    return deck
