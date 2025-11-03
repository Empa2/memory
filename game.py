from pathlib import Path
from enum import Enum
import random
import string
import time
import json

class MemoryGameError(Exception):
    pass

class StateError(MemoryGameError):
    pass

class InvalidMove(MemoryGameError):
    pass

class GameNotStarted(MemoryGameError):
    pass

class CoordinateError(MemoryGameError):
    pass

class DifficultyError(MemoryGameError):
    pass

class CardState(Enum):
    HIDDEN = ("hidden", "kortet är dolt")
    FLIPPED = ("flipped", "kortet är vänt upp")
    MATCHED = ("matched", "kortet är matchat")

    def __init__(self, state, description):
        self.state = state
        self.description = description

class Game:
    def __init__(self, seed=None):
        self.loader = DataLoader()
        self.seed = seed or random.randrange(1000000)
        self.rng = random.Random(self.seed)
        self.board = None
        self.moves = 0
        self.matched_pairs = 0
        self.start_time = None
        self.end_time = None
        self.settings = {"easy": 4, "medium": 6, "hard": 8}

    def start_new_game(self, difficulty):
        if difficulty not in self.settings:
            raise DifficultyError("Ogiltig svårhetsgrad")
        size = self.settings.get(difficulty)
        n_pairs = size*size // 2
        words = self.loader.pick_words(n_pairs, rng=self.rng)
        deck = words*2
        self.rng.shuffle(deck)
        word_len = max((len(w) for w in deck), default=0)

        self.board = Board(size, word_len)
        self.board.create_board(deck)

        self.moves = 0
        self.matched_pairs = 0
        self.start_time = time.time()
        self.end_time = None

    def choose_card(self, coord):
        if self.board is None:
            raise GameNotStarted("Inget aktivt spel. Starta ett nytt spel först.")
        row, col = self.board.parse_position(coord)
        state = self.board.get_state(row, col)
        if state != CardState.HIDDEN:
            raise InvalidMove(f"Rutan {coord} är inte dold (state='{state}').")
        self.board.set_state(row, col, CardState.FLIPPED)
        return row, col

    def match(self, coord_1, coord_2):
        row_1, col_1 = self.board.parse_position(coord_1)
        value_1 = self.board.get_value(row_1, col_1)
        row_2, col_2 = self.board.parse_position(coord_2)
        value_2 = self.board.get_value(row_2, col_2)
        if (self.board.get_state(row_1, col_1) != CardState.FLIPPED
            or self.board.get_state(row_2, col_2) != CardState.FLIPPED):
            raise InvalidMove("Båda korten måste vara uppvända innan matchning.")
        self.moves += 1
        if value_1 == value_2:
            self.board.set_state(row_1, col_1, CardState.MATCHED)
            self.board.set_state(row_2, col_2, CardState.MATCHED)
            self.matched_pairs += 1
            if self.is_finished() and self.end_time is None:
                self.end_time = time.time()
            return True
        else:
            self.board.set_state(row_1, col_1, CardState.HIDDEN)
            self.board.set_state(row_2, col_2, CardState.HIDDEN)
        return False

    def is_finished(self):
        return self.matched_pairs == (self.board.size ** 2) // 2

    def time_elapsed(self):
        if self.start_time is None:
            return 0
        if self.end_time is not None:
            return self.end_time - self.start_time
        return time.time() - self.start_time


class Board:
    def __init__(self, size, word_len):
        self.size = size
        self.word_len = word_len
        self.board = []


    def __str__(self):
        col_w = max(1, self.word_len)
        gap = "  "

        header_letters = gap.join(ch.center(col_w) for ch in string.ascii_uppercase[:self.size])
        header = " " * 4 + header_letters
        lines = [header]
        for r, row in enumerate(self.board, start=1):
            cells = []
            for cell in row:
                if cell["state"] == CardState.HIDDEN:
                    s = "-" * col_w
                else:
                    s = str(cell["value"])[:col_w].ljust(col_w)
                cells.append(s)
            lines.append(f"{r:<2}| " + gap.join(cells))
        return "\n".join(lines)


    def create_board(self, deck):
        if len(deck) != self.size * self.size:
            raise ValueError(f"Fel antal kort: fick {len(deck)}, förväntade {self.size * self.size}.")
        board = []
        k = 0
        for _ in range(self.size):
            row = []
            for _ in range(self.size):
                cell = {"value": deck[k], "state": CardState.HIDDEN}
                row.append(cell)
                k += 1
            board.append(row)
        self.board = board

    def get_cell(self, row, col):
        return self.board[row][col]

    def get_value(self, row, col):
        return self.board[row][col]["value"]

    def get_state(self, row, col):
        return self.board[row][col]["state"]

    def set_state(self, row, col, new_state):
        if self.board[row][col]["state"] == new_state:
            raise StateError(f"Ordet på ({row}, {col}) är redan '{new_state.description}'.")
        if self.board[row][col]["state"] == CardState.MATCHED:
            raise StateError(f"Ordet på ({row}, {col}) är redan matchat.")
        self.board[row][col]["state"] = new_state

    def parse_position(self, coord):
        coord = coord.strip().upper()
        if len(coord) < 2:
            raise CoordinateError("Ange en koordinat, t.ex. A1.")
        col_part = coord[0]
        row_part = coord[1:]

        if not col_part.isalpha():
            raise CoordinateError("Koordinaten måste börja med en bokstav för kolumnen.")

        if not row_part.isdigit():
            raise CoordinateError("Koordinaten måste innehålla en siffra för raden.")

        row = int(row_part) - 1
        col = ord(col_part) - ord("A")

        if row < 0 or row >= self.size or col < 0 or col >= self.size:
            raise CoordinateError("Koordinaten ligger utanför brädet")
        return row, col


class DataLoader:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path or Path(__file__).parent) / "data"
        self.score_path = self.base_path
        self.score_path.mkdir(parents=True, exist_ok=True)

    def load_words(self, filename="memo.txt"):
        path = self.base_path / filename
        with path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            words = [s.encode("latin-1").decode("utf-8") for s in lines]
        return sorted(set(words))

    def pick_words(self, n, rng=None):
        words = self.load_words()
        if words is None or len(words) < n:
            raise ValueError("Inte tillräckligt med ord i ordlistan.")
        if rng is None:
            rng = random
        return rng.sample(words, n)

    def load_score(self, filename="score.json"):
        path = self.score_path / filename
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print("fel format")
                return []

        if not isinstance(data, list):
            return []
        return data

    def save_score(self, result, filename="score.json"):
        path = self.score_path / filename
        score = self.load_score(filename)
        score.append(result)
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as file:
            json.dump(score, file, indent=4, ensure_ascii=False)
        tmp.replace(path)
 