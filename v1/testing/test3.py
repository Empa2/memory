import string


words = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew"]
deck = words * 20


word_2 = ["ett", "två", "tre", "fyra", "fem", "sex", "sju", "åtta"]
deck_2 = word_2 * 2


def create_board(deck):
    board = []
    k = 0
    n = 12  #

    for _ in range(n):
        row = []
        for _ in range(n):
            cell = {"value": deck[k], "state": "hidden"}
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
        print(f"{i+1}{' '*word_len}", end="")
    print()
    letters = string.ascii_uppercase[:len(board)]
    k = 0
    for row in board:
        print(f"{letters[k]} | ", end="")
        k += 1
        for cell in row:
            if cell["state"] == "hidden":
                print(f"{'-' * word_len}", end=" ")
            else:
                print(f"{cell['value'].ljust(word_len)}", end=" ")
        print()


def board_size(board):
    return len(board)


def return_print_board(board, word_len):
    letters = list(string.ascii_uppercase[:board_size(board)])
    header = "       " + " ".join(letter.ljust(word_len) for letter in letters)
    print(letters)
    rows = [header]
    for i, row in enumerate(board, start=1):
        row_cells = []
        for cell in row:
            if cell['state'] != "hidden":
                row_string = cell["value"].ljust(word_len)
            else:
                row_string = ("-"*word_len).ljust(word_len)
            print(cell)
            row_cells.append(row_string)
        print(row_cells)
        row_str = " ".join(row_cells)
        rows.append(f"{i:<2} | {row_str}")
        print(row_str)
        print()
    return "\n".join(rows)


def return_print_board_v2(board, word_len):
    letters = list(string.ascii_uppercase[:board_size(board)])
    header = " "*(word_len//2+5) + " ".join(letter.ljust(word_len) for letter in letters)
    rows = [header]
    for i, row in enumerate(board, start=1):
        row_cells = []
        for cell in row:
            if cell['state'] != "hidden":
                row_string = cell["value"].ljust(word_len)
            else:
                row_string = ("-"*word_len).ljust(word_len)
            row_cells.append(row_string)
        row_str = " ".join(row_cells)
        rows.append(f"{i:<2} | {row_str}")
    return "\n".join(rows)


board = create_board(deck)
#print(board)
world_lenght = word_len(board)
#print_board(board, world_lenght)
#print(return_print_board(board, world_lenght))

print(return_print_board_v2(board, world_lenght))

print("")
#board = create_board(deck_2)
#print(board)
#world_lenght = word_len(board)
#print_board(board, world_lenght)
#print(return_print_board(board, world_lenght))


board[1][1]["state"] = "flipped"
board[2][3]["state"] = "matched"


print(return_print_board_v2(board, world_lenght))

#A = return_print_board(board, word_len(board))
# print(A)