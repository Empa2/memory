from enum import Enum
import string

class CardState(Enum):
    HIDDEN = ("hidden", "kortet är dolt")
    FLIPPED = ("flipped", "kortet är vänt upp")
    MATCHED = ("matched", "kortet är matchat")

    def __init__(self, state, description):
        self.state = state
        self.description = description


words = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew"]
deck = words * 20


word_2 = ["ett", "två", "tre", "fyra", "fem", "sex", "sju", "åtta"]
deck_2 = word_2 * 20


def create_board(deck):
    board = []
    k = 0
    n = 12  #
    
    for _ in range(n):
        row = []
        for _ in range(n):
            cell = {"value": deck[k], "state": CardState.HIDDEN.state}
            row.append(cell)
            k += 1
        board.append(row)
    return board
    # print(board)

def word_len(board):
    return max(len(cell["value"]) for row in board for cell in row)

def print_board(board, word_len):
    print("   " + " "*(word_len//2), end="")
    for i in range(len(board)):
        print(f"{i+1}{" "*word_len}", end="")
    print()
    letters = string.ascii_uppercase[:len(board)]
    k = 0
    for row in board:
        print(f"{letters[k]} | ", end="")
        k += 1
        for cell in row:
            if cell["state"] == CardState.HIDDEN.state:
                print(f"{"-" * word_len}", end=" ")
            else:
                print(f"{cell["value"].ljust(word_len)}", end=" ")
        print()

def board_size(board):
    return len(board)
        


def return_print_board(board, word_len):
    letters = list(string.ascii_uppercase)
    col_width = max(word_len, 2)
    header = " " * (4) + "  ".join(str(i + 1).rjust(col_width) for i in range(board_size(board)))
    rows = [header]
    print(header)
    for i, row in enumerate(board):
        row_str = "  ".join(
            (cell["value"] if cell["state"] != CardState.HIDDEN.state else "-" * word_len).ljust(word_len)
            for cell in row
        )
        rows.append(f"{letters[i]} | {row_str}")
    return "\n".join(rows)
            



board = create_board(deck)
#print(board)
world_lenght = word_len(board)
#print_board(board, world_lenght)
print(return_print_board(board, world_lenght))


board = create_board(deck_2)
#print(board)
world_lenght = word_len(board)
#print_board(board, world_lenght)
print(return_print_board(board, world_lenght))


board[1][1]["state"] = CardState.FLIPPED.state
board[2][3]["state"] = CardState.MATCHED.state

A = return_print_board(board, word_len(board))
print(A)