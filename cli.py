import os
import time
from game import Game, DataLoader, MemoryGameError, CoordinateError

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def pause():
    input("Tryck [Enter] för att fortsätta...")


def get_difficulty():
    while True:
        difficulty = input("Svårhetsgrad (easy, medium, hard): ").strip().lower()
        if difficulty in ("easy", "medium", "hard"):
            return difficulty
        print("Ogiltig svårhetsgrad. Försök igen.")


def get_seed():
    seed = input("seed: ").strip()
    return seed or None


def get_user_name():
    while True:
        user_name = input("Ange ditt namn för highscore-listan"
                          " (Enter om du vill vara anonym): ").strip()
        if len(user_name) > 15:
            print("Namnet är för långt (max 15 tecken). Försök igen!")

        elif not user_name:
            return "Anonym"
        else:
            return user_name


def prompt_coords(game):
    while True:
        choice = input("Välj en ruta t.ex A1 eller A2, B1: ").strip()
        if choice.lower() in ("q", "quit", "exit"):
            print("Avslutar spelet...")
            return None
        try:
            coords = game.parse_coords(choice)
            return coords
        except CoordinateError as e:
            print(f"Fel: {e}\nFörsök igen.")


def play_turn(game, coords):
    if len(coords) != 1:
        raise CoordinateError(f"Tar bara emot en koordinat, du angav {coords}")
    try:
        game.choose_card(coords[0])
        clear_screen()
        print(game.board)
        return True
    except MemoryGameError as e:
        print(f"Ogiltigt drag: {e}")
        return False


def show_highscores():
    loader = DataLoader()
    score = loader.load_score()

    finished_games = [s for s in score if s.get("finished")]

    if not finished_games:
        print("finns inga tidigare higscores")
        return

    finished_games_easy = sorted([s for s in finished_games if s.get("difficulty") == "easy"],
                        key=lambda x: (x.get("moves", float("inf")), x.get("time", float("inf"))))

    finished_games_medium = sorted([s for s in finished_games if s.get("difficulty") == "medium"],
                        key=lambda x: (x.get("moves", float("inf")), x.get("time", float("inf"))))

    finished_games_hard = sorted([s for s in finished_games if s.get("difficulty") == "hard"],
                        key=lambda x: (x.get("moves", float("inf")), x.get("time", float("inf"))))

    i = j = k = 0
    print(f"{'Datum':^10} | {'Namn':^14} | {'Drag':^3} | {'Tid (s)':^6} | {'Plats':^2}")
    print(f"{'Lätt':-^52}")
    for s in finished_games_easy:
        print(f"{s['time_stamp'].split(' ')[0]:<12}"
              f"{s['user_name']:<16} {s['moves']:>5}"
              f"{s['time']:>8.2f} {i+1:>6}")
        i += 1
    print(f"{'Medel':-^52}")
    for s in finished_games_medium:
        print(f"{s['time_stamp'].split(' ')[0]:<12}"
              f"{s['user_name']:<16} {s['moves']:>5}"
              f"{s['time']:>8.2f} {j+1:>6}")
        j += 1
    print(f"{'Svår':-^52}")
    for s in finished_games_hard:
        print(f"{s['time_stamp'].split(' ')[0]:<12}"
              f"{s['user_name']:<16} {s['moves']:>5}"
              f"{s['time']:>8.2f} {k+1:>6}")
        k += 1


def start_game():
    game = Game(get_seed())
    difficulty = get_difficulty()
    game.start_new_game(difficulty)
    clear_screen()
    print(game.board)
    run_game(game)
    result = get_result(game, difficulty)
    game.loader.save_score(result)
    print_result(game, result)
    print("\nResultat sparat i data/score.json")


def run_game(game):
    try:
        coords = []
        while not game.is_finished():
            coord = prompt_coords(game)
            if coord is None:
                break

            for i in coord:
                ok = play_turn(game, [i])
                if ok:
                    coords.append(i)

            if len(coords) == 2:
                matched = game.match(coords[0], coords[1])
                print("Bra jobbat! Du hittade ett par!" if matched else "Tyvärr, det var inget par.")
                pause()
                clear_screen()
                print(game.board)
                coords = []
    except MemoryGameError as error:
        print(f"Ett fel uppstod: {error}")


def get_result(game, difficulty):
    result = {
        "game_id": f"{int(time.time()*1000)}-{game.seed}",
        "seed": game.seed,
        "user_name": get_user_name(),
        "moves": game.moves,
        "difficulty": difficulty,
        "time": round(game.time_elapsed(), 2),
        "finished": game.is_finished(),
        "time_stamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
    return result

def print_result(game, result):

    difficulty = result.get("difficulty")
    loader = DataLoader()
    score = loader.load_score()
    finished_games = [s for s in score if s.get("finished") and s.get("difficulty") == difficulty]
    finished_games_sorted = sorted(finished_games, key=lambda x: (x.get("time", float("inf")), x.get("moves", float("inf"))))
    position = 1 + next((i for i, s in enumerate(finished_games_sorted)
                         if s["game_id"] == result["game_id"]), len(finished_games_sorted))

    if game.is_finished():
        print("\nGrattis! Du har klarat spelet!")
        print(f"Antal drag: {result['moves']}")
        print(f"Tid: {result['time']:.2f} sekunder")
        print(f"Du hamnade på plats {position}, highscore-listan för svårhetsgraden '{difficulty}'.")
    else:
        print("\nSpelet avbröts innan det var klart.")
        print(f"Antal drag: {result['moves']}")
        print(f"Tid: {result['time']:.2f} sekunder")


def start_cli():
    while True:
        clear_screen()
        print("Välkommen till Memory i terminalläge!")
        print("[1]. Starta nytt spel")
        print("[2]. Visa highscore")
        print("[3]. Tillbaka till huvudmenyn")
        choice = input("Välj ett alternativ (1-3): ").strip()
        if choice == "1":
            start_game()
            pause()
        elif choice == "2":
            clear_screen()
            show_highscores()
            pause()
        elif choice == "3":
            print("Tack för att du spelade! Hej då!")
            break
        else:
            print("Ogiltigt val. Försök igen.")
            pause()
