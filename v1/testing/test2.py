import random

n = 4
words = ["a", "b", "c", "d", "e", "f", "g", "h"]
deck = words * 2
random.shuffle(deck)

board = []
k = 0
for r in range(n):
    row = []
    for c in range(n):
        cell = {"value": deck[k], "state": "hidden"}
        row.append(cell)
        k += 1
    board.append(row)


for row in board:
    print("  ".join(cell["value"] for cell in row))

for row in board:
    print("  ".join(cell["state"] for cell in row))

for row in board:
    print(row)

cell = board[1][2]["state"] = "flipped"

for row in board:
    print("  ".join(cell["state"] for cell in row))
