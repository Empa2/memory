from __future__ import annotations
from collections.abc import Iterator
from typing import Any

from enum import Enum, auto
import string
from pathlib import Path
import json
import random
import time


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


class Game:
    def __init__(self, board: Board, difficulty: str, rng: RandomGen) -> None:
        self.board = board
        self.difficulty = difficulty
        self.rng = rng

        self._state: GameState = GameState.WAIT_FIRST
        self._start_timestamp: float | None = None
        self._end_timestamp: float | None = None
        self.moves: int = 0

    def start_new_game(self, deck: list[str]) -> None:
        local_deck = list(deck)
        expected = self.board.size * self.board.size
        if len(local_deck) != expected:
            raise GameError(f"Fel antal kort: fick {len(local_deck)}, förväntade {expected}")

        self.rng.shuffle(local_deck)
        self.board.create_board(local_deck)

        self._state = GameState.WAIT_FIRST
        self.moves = 0
        self._start_timestamp = None
        self._end_timestamp = None

    def state(self) -> GameState:
        return self._state

    def is_finished(self) -> bool:
        return self._state == GameState.FINISHED

    def time_elapsed(self) -> float:
        if self._start_timestamp is None:
            return 0.0
        if self._end_timestamp is not None:
            return self._end_timestamp - self._start_timestamp
        return time.time() - self._start_timestamp

    def current_selection(self) -> list[tuple[int, int]]:
        return self.board.flipped_positions()

    def allowed_moves(self) -> list[tuple[int, int]]:
        if self._state == GameState.WAIT_FIRST:
            return self.board.hidden_positions()

        if self._state == GameState.WAIT_SECOND:
            return self.board.hidden_positions()

        return []

    def can_flip(self, row: int, col: int) -> bool:
        return (row, col) in self.allowed_moves()

    def flip(self, row: int, col: int) -> None:
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
        if self._start_timestamp is None:
            self._start_timestamp = time.time()
        flipped = self.board.flipped_positions()

        if len(flipped) == 1:
            self._state = GameState.WAIT_SECOND
        elif len(flipped) == 2:
            # om två kort är vända så kan man försöka matcha
            self._state = GameState.RESOLVING
        else:
            raise GameError("Internt fel: fler än två kort uppvända")

    def resolve(self) -> dict[str, bool | tuple[int, int]]:
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
          # Alla kort är matchade
            self._state = GameState.FINISHED
            self._end_timestamp = time.time()
        else:
          # Tillbaka till att vänta på första kortet igen
            self._state = GameState.WAIT_FIRST

        return {
            "matched": matched,
            "first": (row1, col1),
            "second": (row2, col2),
        }

    def _all_pairs_matched(self) -> bool:
        return len(self.board.matched_positions()) == self.board.size * self.board.size


class Board:
    def __init__(self, size: int) -> None:
        self.size = size
        self.board: list[list[Card]] = []

        if self.size > 26:
            raise GameError("Storlek över 26 inte tillåtet")

    def create_board(self, deck: list[str]) -> None:
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

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def get_card(self, row: int, col: int) -> Card:
        if not self.in_bounds(row, col):
            raise CoordinateError("Position utanför brädet.")
        return self.board[row][col]

    def iter_cards(self) -> Iterator[Card]:
        for row in self.board:
            for card in row:
                yield card

    def iter_positions(self) -> Iterator[tuple[int, int]]:
        for row in range(self.size):
            for col in range(self.size):
                yield row, col

    def hidden_positions(self) -> list[tuple[int, int]]:
        return [(row, col) for (row, col) in self.iter_positions()
                if self.board[row][col].state == CardState.HIDDEN]

    def flipped_positions(self) -> list[tuple[int, int]]:
        return [(row, col) for (row, col) in self.iter_positions()
                if self.board[row][col].state == CardState.FLIPPED]

    def matched_positions(self) -> list[tuple[int, int]]:
        return [(row, col) for (row, col) in self.iter_positions()
                if self.board[row][col].state == CardState.MATCHED]

    def reset_flipped(self) -> None:
        for row in range(self.size):
            for col in range(self.size):
                card = self.board[row][col]
                if card.state == CardState.FLIPPED:
                    card.set_state(CardState.HIDDEN)

    def parse_coord(self, coord: str) -> tuple[int, int]:
        coord = coord.strip().upper()
        if len(coord) < 2:
            raise CoordinateError("Ange en koordinat, t.ex. A1.")
        col = ord(coord[0]) - ord("A")
        # Kolumnen räknas genom bokstaven: A=0, B=1,
        try:
            row = int(coord[1:]) - 1
        except ValueError as exc: # int ger value Error fånga och ge som CoordinateError
            raise CoordinateError("Ogiltigt radnummer") from exc

        if not self.in_bounds(row, col):
            raise CoordinateError("Koordinaten ligger utanför brädet.")
        return row, col

    def __str__(self) -> str:
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


class Card:
    def __init__(self, value: str) -> None:
        self.value:str = value
        self.state: CardState = CardState.HIDDEN

    def set_state(self, new_state: CardState) -> None:
        if self.state == CardState.MATCHED:
            raise GameStateError("Kan inte ändra state på ett matchat kort.")

        if not isinstance(new_state, CardState):
            raise GameStateError("Ny state måste vara av instans CardState")

        self.state = new_state

    def __repr__(self) -> str:
        return f"Card(value={self.value!r}, state={self.state.name})"


class WordRepository:
    def __init__(self,
                 settings: Settings,
                 base_path: str | Path | None = None,
                 filename: str | None = None,
                 encoding: str ="utf-8"
                 ) -> None:

        self.settings = settings
        self.base_path = Path(base_path or settings.data_dir)
        self.filename = filename or settings.words_file
        self.encoding = encoding
        self._words: list[str] | None = None

    def load_words(self) -> list[str]:
        if self._words is not None:
            return self._words
        path = self.base_path / self.filename
        try:
            with path.open("r", encoding=self.encoding) as f:
                loaded_list = [line.strip() for line in f if line.strip()]
        except FileNotFoundError as e:
            raise GameError(f"Hittade inte ordlistan: {path}") from e

        mojibacke = ("Ã¥", "Ã¤", "Ã¶")
        fixed_words = []
        for s in loaded_list:
            if any(marker in s for marker in mojibacke):
                try:
                    s = s.encode("latin-1").decode("utf-8")
                    # Vissa ord i ordlistan innehåller inte ÅÄÖ utan andra tecken detta
                    # fungerar som en liten work around
                except UnicodeError:
                    pass
            fixed_words.append(s)
        self._words = fixed_words
        return self._words

    def pick_words(self, n: int, rng: RandomGen) -> list[str]:
        words = self.load_words()
        if len(words) < n:
            raise ValueError("Inte tillräckligt med ord i ordlistan.")
        return rng.sample(words, n)


class ScoreRepository:
    def __init__(self, settings: Settings,
                 base_path: str | Path | None = None,
                 filename: str | None = None
                 ) -> None:

        self.settings = settings
        self.base_path = Path(base_path or settings.data_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

        filename = filename or settings.score_file
        self.path: Path = self.base_path / filename

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Score filen är korrupt: {self.path}") from e

            if not isinstance(data, list):
                raise ValueError("Score filen måste innehålla en lista")
        return data

    def append(self, entry: dict[str, Any]) -> None:
        data = self.load()
        data.append(entry)

        tmp = self.path.with_suffix(".tmp")

        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.flush()

        tmp.replace(self.path)

    def top(self, difficulty: str, limit: int | None = None) -> list[dict[str, Any]]:
        if self.settings.allowed_difficulties and difficulty not in self.settings.allowed_difficulties:
            raise ValueError(f"Ogiltig svårighetsgrad: {difficulty}")

        records = [
            s for s in self.load()
            if s.get("finished") and s.get("difficulty") == difficulty]

        records.sort(key=lambda x: (x.get("moves", float("inf")),
                                    x.get("time", float("inf"))))

        if limit is None:
            return records
        return records[:limit]


class Settings:
    def __init__(
        self,
        difficulties: dict[str, int] | None = None,
        words_file: str = "memo.txt",
        score_file: str = "score.json",
        data_dir: str | Path | None = None,
    ) -> None:

        self.difficulties = difficulties or {"easy": 4, "medium": 6, "hard": 8}
        self.allowed_difficulties = set(self.difficulties.keys())

        self.words_file = words_file
        self.score_file = score_file
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"


class RandomGen:
    def __init__(self, seed: int | None = None):
        if seed is None:
            seed = random.randint(0, 1_000_000)

        self.seed: int = seed
        self.rng = random.Random(self.seed)

    def get(self, a: int = 0, b: int = 1_000_000) -> int:
        return self.rng.randint(a, b)

    def shuffle(self, deck: list[str]):
        self.rng.shuffle(deck)

    def sample(self, words: list[str], n: int):
        return self.rng.sample(words, n)


def build_deck(word_repo: WordRepository, n_pairs: int, rng: RandomGen) -> list[str]:
    if not isinstance(n_pairs, int) or n_pairs < 1:
        raise ValueError("n_pairs måste vara ett heltal ≥ 1")

    words = word_repo.pick_words(n_pairs, rng)
    deck = [w for w in words for _ in range(2)]
    # range(2) för att skapa dubbla ord i listan
    return deck