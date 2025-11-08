from enum import Enum, auto

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

    def __repr__(self):
        return f"{self.board}"


words = ["Äpple", "Apelsin", "Päron", "Gurka"]
deck = words*4


bräda = Board(4)
bräda.create_board(deck)
print(bräda)   