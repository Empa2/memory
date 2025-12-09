"""CLI-gränssnitt för Memory-spelet.

Det här modulen innehåller all logik för textbaserat spelande:
menyer, inmatning från användaren, highscore-visning och kopplingen
mot själva spelmotorn i ``main.py``.

Tanken är att main.py håller i spelregler, kortlek och bräde, medan
den här filen sköter "snacket" med spelaren i terminalen.
"""

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
    """Eget undantag för att avbryta ett pågående spel.

    Används när spelaren skriver in 'q' istället för en koordinat,
    så att vi kan hoppa ur spelet på ett kontrollerat sätt.
    """


def clear() -> None:
    """Rensar terminalfönstret.

    Använder rätt kommando beroende på operativsystem (Windows eller Unix).
    Inga värden returneras, den bara "städer upp" innan nästa utskrift.
    """
    os.system("cls" if os.name == "nt" else "clear")


def pause() -> None:
    """Pausar tills spelaren trycker Enter.

    Används efter viktiga utskrifter så att spelaren hinner läsa
    innan skärmen rensas igen.
    """
    input("Tryck [Enter] för att fortsätta...")


def choose_difficulty(settings: Settings) -> str:
    """Låter spelaren välja svårighetsgrad.

    Visar alla svårighetsgrader från inställningarna och loopar tills
    spelaren skriver in ett giltigt val.

    Args:
        settings: Settings-objekt med tillgängliga svårighetsgrader.

    Returns:
        En sträng med vald svårighetsgrad (nyckeln i settings.difficulties).
    """
    while True:
        print("Välj svårigetsgrad:")
        for key in settings.difficulties:
            print(f" - {key}")
        difficulty = input(">>> ").strip().lower()
        if difficulty in settings.difficulties:
            return difficulty
        print("Ogiltig svårigetsgrad")


def ask_coord(board: Board, prompt: str) -> tuple[int, int]:
    """Frågar spelaren efter en koordinat på brädet.

    Spelaren kan skriva t.ex. ``A1`` eller ``b3``, eller ``q`` för att
    avbryta spelet. Koordinaten valideras mot brädet.

    Args:
        board: Det aktuella spelbrädet som används för att tolka koordinater.
        prompt: Text som visas innan inmatning, t.ex. "Drag 1: ".

    Returns:
        En tuple (rad, kolumn) med tolkad koordinat.

    Raises:
        QuitGame: Om spelaren skriver in 'q' för att avbryta.
    """
    while True:
        coord = input(prompt).strip().lower()
        if coord == "q":
            raise QuitGame
        try:
            return board.parse_coord(coord)
        except GameError as e:
            print(f"{e}, [q] för att avsluta")


def ask_valid_flip(game: Game, board: Board, prompt: str) -> tuple[int, int]:
    """Frågar efter en koordinat och gör ett giltigt drag.

    Den här funktionen kombinerar inmatning av koordinat med själva
    ``game.flip``-anropet. Om draget inte är tillåtet visas ett fel
    och spelaren får försöka igen.

    Args:
        game: Det aktuella Game-objektet.
        board: Brädet som används för att tolka koordinater.
        prompt: Text som visas innan inmatning.

    Returns:
        En tuple (rad, kolumn) för den ruta som faktiskt vändes.
    """
    while True:
        row, col = ask_coord(board, prompt)
        try:
            game.flip(row, col)
            return row, col
        except GameError as e:
            print(e)


def get_username() -> str:
    """Hämtar ett spelarnamn för highscore-listan.

    Spelaren kan lämna raden tom för att vara anonym, annars krävs ett
    namn på max 15 tecken. Loopar tills ett giltigt namn angivits.

    Returns:
        En sträng med spelarnamnet, eller 'Anonym' om inget angavs.
    """
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
    """Kör ett helt Memory-spel från start till slut.

    Skapar en ny kortlek baserat på vald svårighetsgrad, startar spelet
    och hanterar alla drag tills spelet är klart eller avbrutet.

    Under spelets gång sköter funktionen utskrift av brädet, inmatning
    av drag och anrop till ``game.resolve`` när två kort har valts.

    Args:
        settings: Inställningar för spelet (t.ex. storlekar per svårighetsgrad).
        word_repo: Repository som används för att bygga upp kortleken.

    Returns:
        Game-objektet efter att spelet avslutats (klart eller avbrutet).
    """
    rng = RandomGen()
    difficulty = choose_difficulty(settings)
    size = settings.difficulties[difficulty]
    n_pairs = (size * size) // 2

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
    """Sparar resultatet från ett spel till highscore-listan.

    Bygger upp en dictionary med spelinformation (drag, tid, namn osv.)
    och skickar in den i ``score_repo`` för att lagras.

    Args:
        username: Namnet som ska kopplas till resultatet.
        score_repo: Repository som hanterar lagring av highscores.
        game: Game-objektet som innehåller data om spelrundan.

    Returns:
        En dictionary med hela score-posten som sparats.
    """
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
    """Visar highscore-listan för alla svårighetsgrader.

    Utskriften formateras som en enkel tabell i terminalen, med datum,
    namn, antal drag, tid och placering. Varje svårighetsgrad får sin
    egen sektion.

    Args:
        settings: Settings-objekt som innehåller vilka svårighetsgrader som finns.
        score_repo: Repository där resultaten är lagrade.
    """
    clear()
    print("\n--- Highscore ---\n")

    date_width = 12
    name_width = 16
    moves_width = 6
    time_width = 9
    place_width = 7
    # testade mig fram med dessa värden
    # mellan rum för utskrift
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
    """Visar en sammanfattning av spelarens resultat efter spelet.

    Tar reda på spelarens placering i highscore-listan för vald
    svårighetsgrad och skriver ut drag, tid och eventuell placering.

    Args:
        game: Game-objektet från senaste spelrundan.
        score_repo: Repository som innehåller highscores.
        entry: Score-posten som nyss sparades för den här spelrundan.

    Raises:
        ValueError: Om difficulty i entry inte är en sträng.
    """
    difficulty = entry.get("difficulty")
    if not isinstance(difficulty, str):  # Säkerställer att difficulty är str (mypy klagar annrs)
        raise ValueError
    finished_games = score_repo.top(difficulty)
    positions = [
        i for i, game in enumerate(finished_games)
        if game.get("game_id") == entry.get("game_id")
    ]
    position = positions[0] + 1 if positions else len(finished_games) + 1


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
    """Startar huvudmenyn för Memory-spelet.

    Skapar alla nödvändiga objekt (inställningar, ordrepo, scorerepo)
    och visar en enkel meny där spelaren kan:

    1. Starta nytt spel
    2. Visa highscores
    3. Avsluta programmet

    Funktionen loopar tills spelaren väljer att avsluta.
    """
    settings = Settings()
    word_repo = WordRepository(settings)
    score_repo = ScoreRepository(settings)
    print("Välkommen till memory spelet i terminalläge")
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
