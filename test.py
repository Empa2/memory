from game import Game, InvalidMove, StateError
import os

game = Game(None)
game.start_new_game("easy")

def clear_screen():
    if os.system == "nt":
        os.system("cls")
    else:
        os.system("clear")

def pause():
    input("Tryck [Enter] för att gissa igen")


while not game.is_finished():
    clear_screen()
    print(game.board)
    coord = input("Välj en ruta (t.ex. A1). Q för att avsluta: ").strip()
    if coord.lower() in ("q", "quit", "exit"):
        break
    try:
        ready = game.choose_card(coord)
        print(game.board)  # visa brädet efter vändning
        result = game.resolve_if_ready()
        if result is True:
            print("Träff! 👏")
        elif result is False:
            print("Ingen träff.")
            pause()  # liten paus så man hinner se korten innan de döljs igen
    except (InvalidMove, ValueError, StateError) as e:
        print(f"Fel: {e}")
        pause()