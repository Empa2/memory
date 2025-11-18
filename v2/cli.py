import os
import time
from game import (
    Settings,
    WordRepository,
    ScoreRepository,
    start_game_for_difficulty,
    CoordinateError,
    InvalidMove,
    GameStateError,
)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("Tryck [Enter] för att fortsätta...")


def choose_difficulty(settings):
    print("Välj svårighetsgrad:")
    for d in settings.difficulties:
        print(f" - {d}")

    while True:
        diff = input(">>> ").strip().lower()
        if diff in settings.allowed_difficulties:
            return diff
        print("Ogiltig svårighetsgrad.")


def prompt_coord(board):
    while True:
        raw = input("Välj en ruta (t.ex A1), eller Q för att avbryta: ").strip()
        if raw.lower() in ("q", "quit", "exit"):
            return None
        try:
            return board.parse_coord(raw)
        except CoordinateError as e:
            print(f"Fel: {e}")


def play_turn(game):
    board = game.board

    # --- Första val ---
    print("\nVälj första kortet.")
    pos1 = prompt_coord(board)
    if pos1 is None:
        return False

    try:
        game.flip(*pos1)
    except (InvalidMove, GameStateError) as e:
        print(f"Fel: {e}")
        return True

    clear()
    print(board)

    # --- Andra val ---
    print("\nVälj andra kortet.")
    pos2 = prompt_coord(board)
    if pos2 is None:
        return False

    try:
        game.flip(*pos2)
    except (InvalidMove, GameStateError) as e:
        print(f"Fel: {e}")
        return True

    clear()
    print(board)
    time.sleep(0.6)  # liten delay för att visa uppvända kort

    # --- Resolve ---
    try:
        result = game.resolve()
    except GameStateError as e:
        print(f"Fel: {e}")
        return True

    matched = result["matched"]
    if matched:
        print("\n Bra jobbat! Du hittade ett par!")
    else:
        print("\n Ingen match.")

    pause()
    clear()
    print(board)
    return True


def show_highscore(settings, score_repo):
    clear()
    print("\n=== Highscore ===\n")

    # Kolumnbredder – du kan justera här om du vill ändra layouten
    DATE_W = 12
    NAME_W = 16
    MOVES_W = 6
    TIME_W = 9
    PLACE_W = 7

    # Huvudrubrik (endast en gång)
    print(
        f"{'Datum':<{DATE_W}}"
        f"{'Namn':<{NAME_W}}"
        f"{'Drag':>{MOVES_W}}"
        f"{'Tid (s)':>{TIME_W}}"
        f"{'Plats':>{PLACE_W}}"
    )

    # En sektion per svårighetsgrad
    total_width = DATE_W + NAME_W + MOVES_W + TIME_W + PLACE_W

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
                f"{date_only:<{DATE_W}}"
                f"{entry['user_name']:<{NAME_W}}"
                f"{entry['moves']:>{MOVES_W}}"
                f"{entry['time']:>{TIME_W}.2f}"
                f"{place:>{PLACE_W}}"
            )
    print()


def run_cli():
    settings = Settings()
    word_repo = WordRepository(settings)
    score_repo = ScoreRepository(settings)

    while True:
        clear()
        print("=== MEMORY ===")
        print("[1] Starta nytt spel")
        print("[2] Visa highscore (TODO)")
        print("[3] Avsluta")

        choice = input("Välj: ").strip()

        if choice == "1":
            difficulty = choose_difficulty(settings)

            game = start_game_for_difficulty(
                settings=settings,
                difficulty=difficulty,
                word_repo=word_repo,
                seed=int(time.time() * 1000),
            )

            clear()
            print(game.board)

            # ---- Spelloop ----
            while not game.is_finished():
                if not play_turn(game):
                    break

            # ---- Resultat ----
            if game.is_finished():
                print("\n🎉 Du klarade spelet!")
                print(f"Drag: {game.moves}")
                print(f"Tid: {game.time_elapsed():.2f} sek")

                # Spara highscore
                name = input("Namn för highscore-listan (Enter = anonym): ").strip() or "Anonym"
                entry = {
                    "game_id": str(int(time.time() * 1000)),
                    "user_name": name,
                    "moves": game.moves,
                    "time": round(game.time_elapsed(), 2),
                    "difficulty": difficulty,
                    "finished": True,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "seed": game.seed,
                }
                score_repo.append(entry)
                print("Resultat sparat!")
                pause()
        elif choice == "2":
            show_highscore(settings, score_repo)
            pause()
        elif choice == "3":
            print("Hej då!")
            break
        else:
            print("Ogiltigt val.")
            pause()


if __name__ == "__main__":
    run_cli()