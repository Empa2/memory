import time

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from main import (
    Game, Board, GameError, CardState,
    GameState, WordRepository, ScoreRepository,
    Settings, RandomGen, build_deck
)

class MemoryApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Memory")
        self.resizable(False, False)

        self.settings = Settings()
        self.word_repo = WordRepository(self.settings)
        self.score_repo = ScoreRepository(self.settings)
        self.game: Game | None = None
        self.board_buttons: dict[tuple[int, int], tk.Button] = {}
        self.input_locked: bool = False
        self.timer_running: bool = False

        self.main_menu_frame = ttk.Frame(self)
        self.difficulty_frame = ttk.Frame(self)
        self.game_frame = ttk.Frame(self)
        self.highscore_frame = ttk.Frame(self)

        self.time_label: ttk.Label | None = None
        self.moves_label: ttk.Label | None = None

        self.build_main_menu()
        self.build_difficulty_frame()
        self.build_highscore_frame()

        self.show_frame(self.main_menu_frame)

    def show_frame(self, frame):
        for f in (self.main_menu_frame, self.difficulty_frame, self.game_frame, self.highscore_frame):
            f.pack_forget()
        frame.pack(fill="both", expand=True, padx=10, pady=10)

    def clear_frame(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def build_main_menu(self):
        self.clear_frame(self.main_menu_frame)
        title = ttk.Label(self.main_menu_frame, text="Memory", font=("TkDefaultFont", 18, "bold"))
        title.pack(pady=(0, 20))

        ttk.Button(
            self.main_menu_frame,
            text="Starta nytt spel",
            command=self.choose_difficulty
        ).pack(fill="x", pady=5)

        ttk.Button(
            self.main_menu_frame,
            text="Visa highscore",
            command=self.show_highscores
        ).pack(fill="x", pady=5)

        ttk.Button(
            self.main_menu_frame,
            text="Avsluta",
            command=self.destroy
        ).pack(fill="x", pady=5)

    def choose_difficulty(self):
        self.build_difficulty_frame()
        self.show_frame(self.difficulty_frame)

    def build_difficulty_frame(self):
        self.clear_frame(self.difficulty_frame)
        ttk.Label(self.difficulty_frame, text="Välj svårighetsgrad", font=("TkDefaultFont", 14, "bold")).pack()

        for difficulties in self.settings.difficulties:
            ttk.Button(
                self.difficulty_frame,
                text=difficulties,
                command=lambda d=difficulties: self.start_new_game(d)
            ).pack(fill="x", pady=3)

        ttk.Button(
            self.difficulty_frame,
            text="Tillbaka",
            command=lambda: self.show_frame(self.main_menu_frame)
        ).pack(fill="x", pady=(15, 0))

    def show_highscores(self) -> None:
        self.build_highscore_frame()
        self.show_frame(self.highscore_frame)

    def build_highscore_frame(self):
        self.clear_frame(self.highscore_frame)
        ttk.Label(self.highscore_frame, text="Highscore", font=("TkDefaultFont", 16, "bold")).pack(pady=(0, 10))

        container = ttk.Frame(self.highscore_frame)
        container.pack(fill="both", expand=True)

        for diff in self.settings.difficulties:
            diff_frame = ttk.LabelFrame(container, text=diff.capitalize())
            diff_frame.pack(fill="x", pady=5)

            records = self.score_repo.top(diff)

            if not records:
                ttk.Label(diff_frame, text="(Inga resultat)").pack(anchor="w", padx=5, pady=2)
                continue

            header = ttk.Label(
                diff_frame,
                text=f"{'Plats':<6} {'Datum':<12} {'Namn':<16} {'Drag':<6} {'Tid (s)':<8}",
                font=("TkDefaultFont", 9, "bold"),
            )
            header.pack(anchor="w", padx=5)

            for place, entry in enumerate(records, start=1):
                timestamp = entry.get("timestamp", "")
                date_only = timestamp.split(" ")[0] if timestamp else ""

                line = (
                    f"{place:<6} "
                    f"{date_only:<12} "
                    f"{entry.get('user_name',''):<16} "
                    f"{entry.get('moves', 0):<6} "
                    f"{entry.get('time', 0.0):<8.2f}"
                )
                ttk.Label(diff_frame, text=line, font=("Courier New", 9)).pack(anchor="w", padx=5)

        ttk.Button(
            self.highscore_frame,
            text="Tillbaka",
            command=lambda: self.show_frame(self.main_menu_frame)
        ).pack(fill="x", pady=(15, 0))

    def start_new_game(self, difficulty):
        rng = RandomGen()
        size = self.settings.difficulties[difficulty]
        n_pairs = (size * size) // 2

        try:
            deck = build_deck(self.word_repo, n_pairs, rng)
        except ValueError as e:
            messagebox.showerror("Fel", f"Kunde inte ladda ord:\n{e}")
            return

        board = Board(size)
        game = Game(board, difficulty, rng)
        game.start_new_game(deck)
        self.game = game

        self.input_locked = False
        self.timer_running = True

        self.build_game_frame()
        self.show_frame(self.game_frame)
        self.update_timer_label()

    def build_game_frame(self):
        self.clear_frame(self.game_frame)
        self.build_game_board()

    def build_game_board(self):
        self.board_buttons.clear()

        topbar = ttk.Frame(self.game_frame)
        topbar.pack(fill="x")

        ttk.Button(topbar, text="Tillbaka till huvudmeny", command=self.abort_game).pack(side="left", padx=10)

        ttk.Label(topbar, text=f"Svårighetsgrad: {self.game.difficulty.capitalize()}").pack(side="left", padx=10)

        self.moves_label = ttk.Label(topbar, text="Drag: 0")
        self.moves_label.pack(side="left", padx=10)

        self.time_label = ttk.Label(topbar, text="Tid: 0.00 s")
        self.time_label.pack(side="left", padx=10)

        board_frame = ttk.Frame(self.game_frame)
        board_frame.pack()

        size = self.game.board.size

        for r in range(size):
            for c in range(size):
                btn = ttk.Button(
                    board_frame,
                    text="",
                    width=12,
                    command=lambda row=r, col=c: self.click_on_card(row, col)
                )
                btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                self.board_buttons[(r, c)] = btn

    def abort_game(self):
        if not self.game:
            self.show_frame(self.main_menu_frame)
            return

        if messagebox.askyesno("Avbryt spel", "Vill du avbryta spelet?"):
            msg = (
                "Spelet avbröts.\n\n"
                f"Antal drag: {self.game.moves}\n"
                f"Tid: {self.game.time_elapsed():.2f} sekunder"
            )
            messagebox.showinfo("Resultat", msg)

            self.timer_running = False
            self.input_locked = False
            self.game = None

            self.show_frame(self.main_menu_frame)

    def click_on_card(self, row, col):
        if self.input_locked or not self.game or self.game.is_finished():
            return

        try:
            self.game.flip(row, col)
        except GameError as e:
            messagebox.showwarning("Fel", str(e))
            return

        self.update_board_view()

        if self.game.state() == GameState.RESOLVING:
            self.input_locked = True
            self.after(500, self.resolve_turn)

    def update_board_view(self):
        for (r, c), btn in self.board_buttons.items():
            card = self.game.board.get_card(r, c)

            if card.state == CardState.HIDDEN:
                btn.config(text="", state=("disabled" if self.input_locked else "normal"))

            elif card.state == CardState.FLIPPED:
                btn.config(text=card.value, state="disabled")

            elif card.state == CardState.MATCHED:
                btn.config(text=card.value, state="disabled")

        if self.moves_label:
            self.moves_label.config(text=f"Drag: {self.game.moves}")

    def resolve_turn(self):
        if not self.game:
            self.input_locked = False
            return

        try:
            self.game.resolve()
        except GameError as e:
            messagebox.showerror("Fel", str(e))
            self.input_locked = False
            return

        self.update_board_view()

        if self.game.is_finished():
            self.timer_running = False
            self.input_locked = True
            self.game_is_finished()
        else:
            self.input_locked = False

    def update_timer_label(self):
        if not self.timer_running or not self.game:
            return

        if self.time_label:
            self.time_label.config(text=f"Tid: {self.game.time_elapsed():.2f} s")

        if not self.game.is_finished():
            self.after(120, self.update_timer_label)

    def game_is_finished(self):
        if not self.game:
            return

        username = self.get_username()
        entry = self.save_score(username, self.game)

        difficulty = str(entry.get("difficulty", ""))

        finished_games = self.score_repo.top(difficulty)

        positions = [
            i for i, game in enumerate(finished_games)
            if game.get("game_id") == entry.get("game_id")
        ]
        position = positions[0] + 1 if positions else len(finished_games) + 1

        msg = (
            "Grattis! Du har klarat spelet!\n\n"
            f"Antal drag: {entry['moves']}\n"
            f"Tid: {entry['time']:.2f} sekunder\n"
            f"Du hamnade på plats {position} på highscorelistan "
            f"för svårighetsgraden '{difficulty}'."
        )
        messagebox.showinfo("Resultat", msg)

    def save_score(self, username, game: Game):
        entry = {
            "game_id": game.rng.get() * int(time.time() * 1000),
            "user_name": username,
            "moves": game.moves,
            "time": game.time_elapsed(),
            "difficulty": game.difficulty,
            "finished": game.is_finished(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "seed": game.rng.seed,
        }
        self.score_repo.append(entry)
        return entry

    def get_username(self):
        while True:
            name = simpledialog.askstring(
                "Highscore",
                "Ange ett namn för highscorelistan\n(lämna tomt för 'Anonym'):"
            )
            if name is None:
                return "Anonym"
            name = name.strip()
            if not name:
                return "Anonym"
            if len(name) <= 15:
                return name
            messagebox.showwarning("Namn för långt", "Namnet får max vara 15 tecken.")


if __name__ == "__main__":
    app = MemoryApp()
    app.mainloop()