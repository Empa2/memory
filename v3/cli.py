import os
import time
from main import (
    Game, Board, GameError,
    GameState, WordRepository, ScoreRepository,
    Settings, RandomGen, build_deck
)


class QuitGame(Exception):
    pass


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("Tryck [Enter] för att fortsätta...")


def choose_difficulty(settings):
    while True:
        print("Välj svårigetsgrad:")
        for key in settings.difficulties:
            print(f" - {key}")
        difficulty = input(">>> ").strip().lower()
        if difficulty in settings.difficulties:
            return difficulty
        print("Ogiltig svårigetsgrad")


def ask_coord(board, prompt):
    while True:
        coord = input(prompt).strip().lower()
        if coord == "q":
            raise QuitGame
        try:
            return board.parse_coord(coord)
        except GameError as e:
            print(e)


def ask_valid_flip(game, board, prompt):
    while True:
        row, col = ask_coord(board, prompt)
        try:
            game.flip(row, col)
            return row, col
        except GameError as e:
            print(e)


def get_username():
    while True:
        username = input(
            "Ange ett namn för highscorelistan "
            "(Enter för att vara anonym): "
        ).strip()
        if not username:
            return "Anonym"
        if len(username) <= 15:
            return username
        print("Namnet får max vara 15 tecken, försök igen.")


def play_game(settings, word_repo):
    rng = RandomGen()
    difficulty = choose_difficulty(settings) 
    size = settings.difficulties[difficulty]
    n_pairs = (size*size)//2

    deck = build_deck(word_repo, n_pairs, rng)
    board = Board(size)
    game = Game(board, difficulty, rng)
    game.start_new_game(deck)
    try:
        while not game.is_finished():
            print(board)
            ask_valid_flip(game, board, "Drag 1: ")
            clear()
            print(board)
            ask_valid_flip(game, board, "Drag 2: ")
            clear()
            print(board)
            pause()
            clear()

            if game.state() == GameState.RESOLVING:
                try:
                    game.resolve()
                except GameError as e:
                    print(e)
    except QuitGame:
        print("Avslutar spel...")
    return game


def save_score(username, score_repo, game):
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
    score_repo.append(entry)
    return entry


def show_highscore(settings, score_repo):
    clear()
    print("\n=== Highscore ===\n")

    DATE_WIDTH = 12
    NAME_WIDTH = 16
    MOVES_WIDTH = 6
    TIME_WIDTH = 9
    PLACE_WIDTH = 7

    total_width = (DATE_WIDTH + NAME_WIDTH + MOVES_WIDTH + TIME_WIDTH + PLACE_WIDTH)

    print(
        f"{'Datum':<{DATE_WIDTH}}"
        f"{'Namn':<{NAME_WIDTH}}"
        f"{'Drag':>{MOVES_WIDTH}}"
        f"{'Tid (s)':>{TIME_WIDTH}}"
        f"{'Plats':>{PLACE_WIDTH}}"
    )

    for difficulty in settings.difficulties:

        print(f"\n{difficulty.upper():-^{total_width}}")

        records = score_repo.top(difficulty)

        if not records:
            print("(Inga resultat)")
            continue

        for place, entry in enumerate(records, start=1):
            timestamp = entry.get("timestamp")
            date_only = timestamp.split(" ")[0] if timestamp else ""

            print(
                f"{date_only:<{DATE_WIDTH}}"
                f"{entry['user_name']:<{NAME_WIDTH}}"
                f"{entry['moves']:>{MOVES_WIDTH}}"
                f"{entry['time']:>{TIME_WIDTH}.2f}"
                f"{place:>{PLACE_WIDTH}}"
            )
    print()


def show_result(game, score_repo, entry):
    difficulty = entry.get("difficulty")
    finished_games = score_repo.top(difficulty)
    position = 1 + next(
        (i for i, s in enumerate(finished_games)
         if s.get("game_id") == entry.get("game_id")),
        len(finished_games)
    )

    if game.is_finished():
        print("\nGrattis! Du har klarat spelet!")
        print(f"Antal drag: {entry['moves']}")
        print(f"Tid: {entry['time']:.2f} sekunder")
        print(f"Du hamnade på plats {position}, "
              f"highscore-listan för svårighetsgraden '{difficulty}'.")
    else:
        print("\nSpelet avbröts innan det var klart.")
        print(f"Antal drag: {entry['moves']}")
        print(f"Tid: {entry['time']:.2f} sekunder")


def main():
    settings = Settings()
    word_repo = WordRepository(settings)
    score_repo = ScoreRepository(settings)
    while True:
        print(
            "1. Starta nytt spel\n"
            "2. Visa highscores\n"
            "3. Avsluta"
        )
        choice = input(">>> ").strip().lower()
        if choice == "1":
            game = play_game(settings, word_repo)
            username = get_username()
            score = save_score(username, score_repo, game)
            show_result(game, score_repo, score)
            pause()

        elif choice == "2":
            show_highscore(settings, score_repo)
            pause()

        elif choice == "3":
            print("Avslutar...")
            break
        else:
            print("Ogiltigt val.")
            pause()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nAvslutar...")