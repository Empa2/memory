from enum import Enum, auto
import string
import time
import random

class CardState(Enum):
    HIDDEN = auto()
    FLIPPED = auto()
    MATCHED = auto()

class GameState(Enum):
    WAIT_FIRST = auto()
    WAIT_SECOND = auto()
    RESOLVING = auto()
    FINISHED = auto()

class InvalidMove(Exception):
    pass

class Card:
    def __init__(self, value):
        self.value = value
        self.state = CardState.HIDDEN

    def is_hidden(self):
        return self.state == CardState.HIDDEN
    
    def is_flipped(self):
        return self.state == CardState.FLIPPED
    
    def is_matched(self):
        return self.state == CardState.MATCHED
    
    def set_state(self, new_state):
        if self.state == CardState.MATCHED and new_state != CardState.MATCHED:
            raise ValueError("Kan inte ändra state på ett matchat kort.")

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
            raise ValueError(f"Fel antal kort: fick {len(values)}, förväntade {expected}")
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
            raise IndexError("Position utanför brädet.")
        return self.board[row][col]

    def in_bounds(self, row, col):
        return 0 <= row < self.size and 0 <=col < self.size
 
    def iter_cards(self):
        for row in self.board:
            for card in row:
                yield card

    def all_cards(self):
        return list(self.iter_cards())

    def iter_position(self):
        for row in range(self.size):
            for col in range(self.size):
                yield row, col

    def hidden_positions(self):
        return [(row, col) for (row, col) in self.iter_position() if self.board[row][col].state == CardState.HIDDEN]

    def flipped_positions(self):
        return [(row, col) for (row, col) in self.iter_position() if self.board[row][col].state == CardState.FLIPPED]

    def matched_positions(self):
        return [(row, col) for (row, col) in self.iter_position() if self.board[row][col].state == CardState.MATCHED]

    def value_matrix(self):
        return tuple(tuple(card.value for card in row) for row in self.board)

    def state_matrix(self):
        return tuple(tuple(card.state for card in row) for row in self.board)
    
    def reset_flipped(self):
        for row in range(self.size):
            for col in range(self.size):
                card = self.board[row][col]
                if card.state == CardState.FLIPPED:
                    card.set_state(CardState.HIDDEN)

    def __str__(self):
        longest = max(len(card.value) for card in self.iter_cards())
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
    def __init__(self, board, seed=None, rng=None):
        self.board = board
        self.seed = seed
        self.rng = rng or random.Random(seed)

        self._state = GameState.WAIT_FIRST
        self._start_ts = None
        self._end_ts = None
        self.moves = 0
    
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
            allowed = set(self.board.hidden_positions())
            flipped = self.board.flipped_positions()

            if len(flipped) == 1:
                allowed.discard(flipped[0])
            
            return list(allowed)
        return []
    
    def can_flip(self, row, col):
        return (row, col) in self.allowed_moves()
    
    def flip(self, row, col):
        if self._state not in (GameState.WAIT_FIRST, GameState.WAIT_SECOND):
            raise InvalidMove("Kan inte vända kort i detta läge.")
        
        if not self.board.in_bounds(row, col):
            raise InvalidMove("Positionen ligger utanför brädet.")
        
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
            raise RuntimeError("Internt fel: fler än två kort uppvända")

    def resolve(self):
        if self._state != GameState.RESOLVING:
            raise InvalidMove("Kan inte Resolve i detta läge")
        
        flipped = self.board.flipped_positions()
        if len(flipped) != 2:
            raise RuntimeError("Internt fel: resolve utan två uppvända kort")
        
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