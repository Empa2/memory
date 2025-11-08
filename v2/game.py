from enum import Enum, auto
import string

class CardState(Enum):
    HIDDEN = auto()
    FLIPPED = auto()
    MATCHED = auto()


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
        return tuple(tuple(card.value for card in row) for row in self.board)
    
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
                    cell_str = card.value.ljust(self)
                else:
                    cell_str = ("-"*self).ljust(self)
                row_cells.append(cell_str)
            row_str = " ".join(row_cells)
            rows.append(f"{i:<2} | {row_str}")
        return "\n".join(rows)
    

# Liten lista med ord (8 par = 16 kort)
words = [
    "sol", "måne", "hav", "skog",
    "vind", "sand", "moln", "regn",
    "sol", "måne", "hav", "skog",
    "vind", "sand", "moln", "regn",
]

# --- Skapa bräde ---
board = Board(4)
board.create_board(words)

print("=== Startläge ===")
print(board)

# --- Ändra lite state ---
# Flippa två kort och matcha ett av dem:
board.get_card(0, 0).set_state(CardState.FLIPPED)
board.get_card(0, 1).set_state(CardState.FLIPPED)

# Låtsas att de matchade
board.get_card(1, 1).set_state(CardState.MATCHED)

print("\n=== Efter ändringar ===")
print(board)



