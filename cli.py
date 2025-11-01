from game import Game, InvalidMove, DataLoader
import os
import time


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



def prompt_coords(game):
    while True:
        choice = input("Välj en ruta t.ex A1 eller A2, B1: ").strip()
        if choice.lower() in ("q", "quit", "exit"):
            print("Avslutar spelet...")
            return None
        try:
            coords = parse_coords(game.board, choice)
            return coords
        except ValueError as e:
            print(f"Fel: {e}\nFörsök igen.")


def parse_coords(board, coords):
    if not coords or not coords.strip():
        raise ValueError("Du måste ange minst en ruta.")
    coord = coords.replace(",", " ").split()
    coord = [k.strip() for k in coord if k.strip()]
    print(coord)
    if len(coord) == 0:
        raise ValueError("Inmatningen är tom.")
    if len(coord) > 2:
        raise ValueError("Ange högst två rutor (t.ex. 'A1 B2').")

    if len(coord) == 2 and coord[0] == coord[1]:
        raise ValueError("Du kan inte välja samma ruta två gånger.")

    for coordinate in coord:
        try:
            board.parse_position(coordinate)
        except ValueError as error:
            raise error

    return coord


def play_turn(game, coords):
    if len(coords) != 1:
        raise ValueError(f"Tar bara emot en koordinat, du angav {coords}, ")
    try:
        game.choose_card(coords[0])
        clear_screen()
        print(game.board)
        return True
    except InvalidMove as e:
        print(f"Ogiltigt drag: {e}")
        return False


def show_highscores():
    loader = DataLoader()
    score = loader.load_score()

    finished_games = [s for s in score if s.get("finished")]

    finished_games_easy = sorted([s for s in finished_games if s.get("difficulty") == "easy"],
                                 key=lambda x: (x.get("time", float("inf")), x.get("moves", float("inf"))))

    finished_games_medium = sorted([s for s in finished_games if s.get("difficulty") == "medium"],
                                    key=lambda x: (x.get("time", float("inf")), x.get("moves", float("inf"))))

    finished_games_hard = sorted([s for s in finished_games if s.get("difficulty") == "hard"],
                                 key=lambda x: (x.get("time", float("inf")), x.get("moves", float("inf"))))

    print(f"{'Datum':^10} | {'Namn':^14} | {'Drag':^3} | {'Tid (s)':^6}")
    print(f"{'Lätt':-^44}")
    for s in finished_games_easy:  
        print(f"{s['time_stamp'].split(' ')[0]:<12} {s['user_name']:<16} {s['moves']:>5} {s['time']:>8.2f}")

    print(f"{'Medel':-^44}")
    for s in finished_games_medium:
        print(f"{s['time_stamp'].split(' ')[0]:<12} {s['user_name']:<16} {s['moves']:>5} {s['time']:>8.2f}")

    print(f"{'Svår':-^44}")
    for s in finished_games_hard:
        print(f"{s['time_stamp'].split(' ')[0]:<12} {s['user_name']:<16} {s['moves']:>5} {s['time']:>8.2f}")


def start_game():
    game = Game(get_seed())
    difficulty = get_difficulty()
    game.start_new_game(difficulty)
    coords = []
    clear_screen()
    print(game.board)

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
    game.loader.save_score(result)
    print("\nResultat sparat i data/score.json")



def get_user_name():
    while True:
        user_name = input("Ange ditt namn för highscore-listan (Enter om du vill vara anonym): ").strip()
        if len(user_name) > 15:
            print("Namnet är för långt (max 15 tecken). Försök igen!")

        elif not user_name:
            return "Anonym"
        else:
            return user_name

def start_cli():
    while True:
        clear_screen()
        print("Välkommen till Memory i terinalläge!")
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
