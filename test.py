from game import Game, InvalidMove, StateError

game = Game(None)
game.start_new_game("easy")


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
                if matched:
                    print("Bra jobbat! Du hittade ett par!")
                else:
                    print("Tyvärr, det var inget par.")
                print(game.board)
                coords = []
    except Exception as error:
        print(f"Ett fel uppstod: {error}")


def prompt_coords(game):
    while True:
        choice = input("Välj en ruta t.ex A1 eller A2, B1: ")
        try:
            coords = parse_coords(game.board, choice)
            return coords
        except ValueError as e:
            print(f"Fel: {e}\nFörsök igen.")


def parse_coords(board, coords):
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
    try:
        game.choose_card(coords[0])
        print(game.board)
        return True
    except InvalidMove as e:
        print(f"Ogiltigt drag: {e}")
        return False
    
run_game(game)