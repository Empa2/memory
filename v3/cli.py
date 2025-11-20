from __future__ import annotations
from typing import Any

import os
import time
from main import (
    Game, Board, GameError,
    GameState, WordRepository, ScoreRepository,
    Settings, RandomGen, build_deck
)


class QuitGame(Exception):
    pass


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def pause() -> None:
    input("Tryck [Enter] för att fortsätta...")


def choose_difficulty(settings: Settings) -> str:
    while True:
        print("Välj svårigetsgrad:")
        for key in settings.difficulties:
            print(f" - {key}")
        difficulty = input(">>> ").strip().lower()
        if difficulty in settings.difficulties:
            return difficulty
        print("Ogiltig svårigetsgrad")


def ask_coord(board: Board, prompt: str) -> tuple[int, int]:
    while True:
        coord = input(prompt).strip().lower()
        if coord == "q":
            raise QuitGame
        try:
            return board.parse_coord(coord)
        except GameError as e:
            print(e)


def ask_valid_flip(game: Game, board: Board, prompt: str) -> tuple[int, int]:
    while True:
        row, col = ask_coord(board, prompt)
        try:
            game.flip(row, col)
            return row, col
        except GameError as e:
            print(e)


def get_username() -> str:
    while True:
        username = input(
            "Ange ett namn för highscorelistan "
            "(Enter för att vara anonym): "
        ).strip()
        if not username:
            return "Anonym"
        if len(username) <= 15:
            # max längd 15 efter som vi ger namn 16 platser så har man lite marginal
            return username
        print("Namnet får max vara 15 tecken, försök igen.")


def play_game(settings: Settings, word_repo: WordRepository) -> Game:
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


def save_score(username: str, score_repo: ScoreRepository, game: Game) -> dict[str, Any]:
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


def show_highscore(settings: Settings, score_repo: ScoreRepository) -> None:
    clear()
    print("\n--- Highscore ---\n")

    date_width = 12
    name_width = 16
    moves_width = 6
    time_width = 9
    place_width = 7
    # testade mig fram
    total_width = (date_width + name_width +
                   moves_width + time_width +
                   place_width)

    print(
        f"{'Datum':<{date_width}}"
        f"{'Namn':<{name_width}}"
        f"{'Drag':>{moves_width}}"
        f"{'Tid (s)':>{time_width}}"
        f"{'Plats':>{place_width}}"
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
                f"{date_only:<{date_width}}"
                f"{entry['user_name']:<{name_width}}"
                f"{entry['moves']:>{moves_width}}"
                f"{entry['time']:>{time_width}.2f}"
                f"{place:>{place_width}}"
            )
    print()


def show_result(game: Game, score_repo: ScoreRepository, entry: dict[str, Any]) -> None:
    difficulty = entry.get("difficulty")
    if not isinstance(difficulty, str): # Säkerställer att difficulty är str (mypy klagar annrs)
        raise ValueError
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


def main() -> None:
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
