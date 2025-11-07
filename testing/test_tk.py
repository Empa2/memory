import tkinter as tk

root = tk.Tk()
root.title("Dynamisk n x n-matris av knappar")

n = 4
buttons = []
word_list = ["a", "b", "c", "d", "e", "f", "g", "h"]
deck = word_list*2


for i in range(n):
    root.grid_rowconfigure(i, weight=1, uniform="row")
    root.grid_columnconfigure(i, weight=1, uniform="col")

k = 0
for r in range(n):
    row = []
    for c in range(n):
        btn = tk.Button(root, text=f"{deck[k]}",
                        command=lambda r=r, c=c: print(f"Klick på {r},{c}"))
        btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
        k += 1
        row.append(btn)
    buttons.append(row)

root.minsize(500, 300)
root.mainloop()



"""
import tkinter as tk

def start_game(size):
    """Körs när man valt svårighetsgrad."""
    print(f"Startar nytt spel med brädstorlek {size}x{size}")
    show_board(size)

def show_board(size):
    """Byter skärm och visar ett bräde i rätt storlek."""z
    # Rensa tidigare widgets
    for widget in root.winfo_children():
        widget.destroy()

    # Bygg ett enkelt rutnät med knappar
    for r in range(size):
        for c in range(size):
            btn = tk.Button(root, text=f"{r},{c}", width=4, height=2)
            btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")

    # Gör rutnätet responsivt
    for i in range(size):
        root.grid_rowconfigure(i, weight=1)
        root.grid_columnconfigure(i, weight=1)

# --- GUI start ---
root = tk.Tk()
root.title("Välj svårighetsgrad")

# Gör en "startskärm"
tk.Label(root, text="Välj svårighetsgrad:", font=("Arial", 14)).pack(pady=10)

# Tre knappar för svårighetsgrader
tk.Button(root, text="Easy (4x4)", width=15, command=lambda: start_game(4)).pack(pady=5)
tk.Button(root, text="Medium (6x6)", width=15, command=lambda: start_game(6)).pack(pady=5)
tk.Button(root, text="Hard (8x8)", width=15, command=lambda: start_game(8)).pack(pady=5)

root.minsize(300, 300)
root.mainloop()

"""