from game import Game, Board, DataLoader
import os


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def pause():
    input("Tryck [Enter] för att fortsätta...")


def start_game():
    game = Game(get_seed())
    game.start_new_game(get_difficulty())

    while not game.is_finished():
        clear_screen()
        print(game.board)

        coords = prompt_coords(game)
        if coords is None:
            break

        for coord in coords


def prompt_coords(game):
    while True:
        choice = input("Välj en ruta t.ex A1 eller A2, B1: ").strip()
        if choice.lower in ("q", "quit", "exit"):
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
    game.choose_card(coords[0])
    print(game.board)


def get_difficulty():
    difficulty = input("Svårhetsgrad (easy, medium, hard): ").lower()
    return difficulty

def get_seed():
    seed = input("seed: ").strip()
    if seed.strip() is None:
        return None
    return seed


start_game()
