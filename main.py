from cli import start_cli, clear_screen, pause

def main():
    while True:
        clear_screen()
        print("\nVälkommen till memory-spelet!\n"
            "[1] För att starta terminalversionen av spelet\n"
            "[2] För att starta GUI-versionen av spelet\n"
            "[3] För att avsluta programmet\n")
   
        choice = input("Välj ett alternativ\n>>>: ")
        if choice == "1":
            start_cli()
        elif choice == "2":
            print("Inte implementerat än!")
            pause()
        elif choice == "3":
            print("Avslutar promgrammet...")
            break
        else:
            print("Ogiltigt val, försök igen.")


if __name__ == "__main__":
    main()