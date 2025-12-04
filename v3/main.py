"""P-Uppgift 193 Memory DD1310
    Ett enkelt memory-spel med ord, högstapoänglista och svårighetsgrader.

    Författare: Emil Rosén

    Modulen innehåller
        - Spelloopen och logik (Game, Board, Card)
        - Hantering av ordlistor (WordRepository)
        - Hantering av highscores (ScoreRepository)
        - Inställningar (Settings)
        - Slumptalsgenerator med deterministiskt seed (RandomGen)
        - En hjälpfunktion för att bygga en kortlek (build_deck)
    """

from __future__ import annotations
from typing import Any

from enum import Enum, auto
import string
from pathlib import Path
import json
import random
import time


class CardState(Enum):
    """Möjliga tillstånd för ett kort på brädet."""
    HIDDEN = auto()
    FLIPPED = auto()
    MATCHED = auto()

class GameState(Enum):
    """Möjliga tillstånd för spelet."""
    WAIT_FIRST = auto()
    WAIT_SECOND = auto()
    RESOLVING = auto()
    FINISHED = auto()

class GameError(Exception):
    """Basklass för alla spelrelaterade fel"""
class InvalidMove(GameError):
    """Fel som kastas vid ogiltiga drag"""
class CoordinateError(GameError):
    """Fel som kastas vid ogiltiga koordinater"""
class GameStateError(GameError):
    """Fel som kastas vid fel i speltillstånd"""


class Game:
    """Hanterar logiken och regler för ett memory spel

    Håller koll på brädet, speltilstånd, antal drag och
    tid, för en spelomgång
    """
    def __init__(self, board: Board, difficulty: str, rng: RandomGen) -> None:
        """skapar ett nytt Game objekt
        
        Args:
            board (Board): Brädan som ska spelas på
            difficulty (str): En svårhetsgrad t.ex ("easy")
            rng (Randomgen): För att generera slumptal
        """
        self.board = board
        self.difficulty = difficulty
        self.rng = rng

        self._state: GameState = GameState.WAIT_FIRST
        self._start_timestamp: float | None = None
        self._end_timestamp: float | None = None
        self.moves: int = 0

    def start_new_game(self, deck: list[str]) -> None:
        """Startar en ny spelomgång, med en given ord lista (deck)

        blandar ordlistan, lägger ut orden i och förbereder spelet

        Args:
            deck (list[str]): Lista med ord, måste vara size*size
        Raises:
            GameError: Om antal kort inte är size*size
        """
        local_deck = list(deck)
        expected = self.board.size * self.board.size
        if len(local_deck) != expected:
            raise GameError(f"Fel antal kort: fick {len(local_deck)}, förväntade {expected}")

        self.rng.shuffle(local_deck)
        self.board.create_board(local_deck)

        self._state = GameState.WAIT_FIRST
        self.moves = 0
        self._start_timestamp = None
        self._end_timestamp = None

    def state(self) -> GameState:
        """Retunerar nuvarade spel tillstånd"""
        return self._state

    def is_finished(self) -> bool:
        """Retunerar True om spelet är klart annars False"""
        return self._state == GameState.FINISHED

    def time_elapsed(self) -> float:
        """Retunerar hur lång tid spelet har pågått i sekunder
        
        Om inget spel startat eller inget drag gjorts retuneras 0.0
        """
        if self._start_timestamp is None:
            return 0.0
        if self._end_timestamp is not None:
            return self._end_timestamp - self._start_timestamp
        return time.time() - self._start_timestamp

    def current_selection(self) -> list[tuple[int, int]]:
        """Retunerar koordinaterna för alla tillfället vända (Flipped) kort"""
        return self.board.flipped_positions()

    def allowed_moves(self) -> list[tuple[int, int]]:
        """Retunerar en lista med koordinater som är tillåtna
        
            Endast dolda (Hidden) kort är tillåtna att vända, och bara då
            spelets tillstånd är (WAIT_FIRST eller WAIT_SECOND)"""
        if self._state == GameState.WAIT_FIRST:
            return self.board.hidden_positions()

        if self._state == GameState.WAIT_SECOND:
            return self.board.hidden_positions()

        return []

    def can_flip(self, row: int, col: int) -> bool:
        """Retunerar True om kortet på (row, col) får vändas annars False"""
        return (row, col) in self.allowed_moves()

    def flip(self, row: int, col: int) -> None:
        """Vänd ett kort på given position.
        
        Uppdaterar speltillstådent beroende på om det är fösta eller andra draget. 
        Timern startas vid första draget i spelet.
        
        Args:
            row (int): Radindex för kortet
            col (int): Kolumnindex för kortet
            
        Raises:
            GameStateError: Om man försöker vända kort i feltillstånd
            CoordinateError: Om positionen är utan för brädet
            InvalidMove: Om draget inte är tillåtet eller kortet inte är dolt
            GameError: Om något internt blir fel, tex fler en två uppvända kort"""
        if self._state not in (GameState.WAIT_FIRST, GameState.WAIT_SECOND):
            raise GameStateError("Kan inte vända kort i detta läge.")

        if not self.board.in_bounds(row, col):
            raise CoordinateError("Positionen ligger utanför brädet.")

        if not self.can_flip(row, col):
            raise InvalidMove("Ogiltigt drag just nu.")

        card = self.board.get_card(row, col)
        if card.state != CardState.HIDDEN:
            raise InvalidMove("Kortet är inte dolt")

        card.set_state(CardState.FLIPPED)
        if self._start_timestamp is None:
            self._start_timestamp = time.time()
        flipped = self.board.flipped_positions()

        if len(flipped) == 1:
            self._state = GameState.WAIT_SECOND
        elif len(flipped) == 2:
            # om två kort är vända så kan man försöka matcha
            self._state = GameState.RESOLVING
        else:
            raise GameError("Internt fel: fler än två kort uppvända")

    def resolve(self) -> None:
        """Försöker para ihop det två uppvända korten,
        
            Jämför de två uppvända korten (Flipped), uppdaterar deras tillstånd
            till MATCHED om de har samma value, annars HIDDEN och spel tillståndet
            går till WAIT_FIRST. Antal drag (moves) ökar med 1. Om alla par är hittade
            så sätts speltilstånd till FINISHED
            
            Raises:
                GameStateError: Om resolve anropas i fel speltilstånd
                GameError: Om antal kort uppvända inte är exakt två"""
        if self._state != GameState.RESOLVING:
            raise GameStateError("Kan inte Resolve i detta läge")

        flipped = self.board.flipped_positions()
        if len(flipped) != 2:
            raise GameError("Internt fel: resolve utan två uppvända kort")

        (row1, col1), (row2, col2) = flipped
        card1 = self.board.get_card(row1, col1)
        card2 = self.board.get_card(row2, col2)

        matched = card1.value == card2.value

        self.moves += 1

        if matched:
            card1.set_state(CardState.MATCHED)
            card2.set_state(CardState.MATCHED)

        else:
            self.board.reset_flipped()

        if self._all_pairs_matched():
          # Alla kort är matchade
            self._state = GameState.FINISHED
            self._end_timestamp = time.time()
        else:
          # Tillbaka till att vänta på första kortet igen
            self._state = GameState.WAIT_FIRST

    def _all_pairs_matched(self) -> bool:
        """Retunerar True om alla kort på brädet är uppvända annars False"""
        return len(self.board.matched_positions()) == self.board.size * self.board.size


class Board:
    """Representerar en bräda med en matris av Card objekt"""
    def __init__(self, size: int) -> None:
        """Skapar en bräda med given storlek
        
        Args:
            size(int): Antal rader och kolumner (size x size)

        Raises:
            GameError om en större storlek än 26 (Tillåter bara kolummer med bokstäver A-Z)"""
        self.size = size
        self.board: list[list[Card]] = []

        if self.size > 26:
            raise GameError("Storlek över 26 inte tillåtet")

    def create_board(self, deck: list[str]) -> None:
        """Skapa en bräda med ord givet lista med ord
        
        Args:
            deck list[str]: Lista med kortvärden, antal ord (längden på listan) 
            måste vara size x size
            
        Raises:
            GameError: Om antal kort inte matchar med brädans storlek"""
        values = list(deck)
        expected = self.size * self.size
        if len(values) != expected:
            raise GameError(f"Fel antal kort: fick {len(values)}, förväntade {expected}")
        it = iter(values)
        board = []
        for _ in range(self.size):
            row = []
            for _ in range(self.size):
                value = next(it)
                row.append(Card(value))
            board.append(row)
        self.board = board

    def in_bounds(self, row: int, col: int) -> bool:
        """Retunerar True om (row, col) är på brädan annars False"""
        return 0 <= row < self.size and 0 <= col < self.size

    def get_card(self, row: int, col: int) -> Card:
        """Hämtar kortet på angiven position
            
            Args:
                row (int): Radindex
                col (int): Kolumnindex

            Raises:
                CoordinateError: om positionen är utanför brädan
            
            Returns:
                Card objekt för positionen"""
        if not self.in_bounds(row, col):
            raise CoordinateError("Position utanför brädet.")
        return self.board[row][col]

    def hidden_positions(self) -> list[tuple[int, int]]:
        """Retunerar en lista med koordinater för alla dolda kort (HIDDEN)"""
        result: list[tuple[int, int]] = []
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col].state == CardState.HIDDEN:
                    result.append((row, col))
        return result

    def flipped_positions(self) -> list[tuple[int, int]]:
        """Retunerar en lista med koordinater för alla gissade kort (FLIPPED)"""
        result: list[tuple[int, int]] = []
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col].state == CardState.FLIPPED:
                    result.append((row, col))
        return result

    def matched_positions(self) -> list[tuple[int, int]]:
        """Retunerar en lista med koordinater för alla matchade kort (MATCHED)"""
        result: list[tuple[int, int]] = []
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col].state == CardState.MATCHED:
                    result.append((row, col))
        return result

    def reset_flipped(self) -> None:
        """Vänder tillbaka alla kort som är gissade kort (FLIPPED) till dola (HIDDEN)"""
        for row in range(self.size):
            for col in range(self.size):
                card = self.board[row][col]
                if card.state == CardState.FLIPPED:
                    card.set_state(CardState.HIDDEN)

    def parse_coord(self, coord: str) -> tuple[int, int]:
        """Översätter text koordinater till intern baserad (row, col)
        
            En koordinat tolkas som en bokstav, (Kolumn) följt av en heltal (Rad)
            t.ex 'A1' -> (0, 0), 'B3' -> (2, 1)
        
        Args:
            Coord (str): En koordinat från användar koordinat som ska översättas

        Raises:
            CoordinateError: Om formatet är fel, eller positionen är utanför brädan
        
        Returns: 
            tuple(row: int, col: int) med noll-baserat index"""
        coord = coord.strip().upper()
        if len(coord) < 2:
            raise CoordinateError("Ange en koordinat, t.ex. A1.")
        col = ord(coord[0]) - ord("A")
        # Kolumnen räknas genom bokstaven: A=0, B=1
        try:
            row = int(coord[1:]) - 1
        except ValueError as exc: # int ger value Error fånga och ge som CoordinateError
            raise CoordinateError("Ogiltigt radnummer") from exc

        if not self.in_bounds(row, col):
            raise CoordinateError("Koordinaten ligger utanför brädet.")
        return row, col

    def __str__(self) -> str:
        "Retunerar en sträng representation av brädan för utskrift."
        if not self.board:
            return "<tomt bräde>"

        longest = max(len(str(card.value)) for row in self.board for card in row)
        letters = list(string.ascii_uppercase[:self.size])
        header = " "*(longest//2+5) + " ".join(letter.ljust(longest) for letter in letters)
        rows = [header]
        for i, row in enumerate(self.board, start=1):
            row_cells = []
            for card in row:
                if card.state != CardState.HIDDEN:
                    cell_str = str(card.value).ljust(longest)
                else:
                    cell_str = ("-"*longest).ljust(longest)
                row_cells.append(cell_str)
            row_str = " ".join(row_cells)
            rows.append(f"{i:<2} | {row_str}")
        return "\n".join(rows)


class Card:
    """Representerar ett kort i spelet"""
    def __init__(self, value: str) -> None:
        """Skapar ett nytt kort i dolt tillstånd
        
        Args:
            Value (str): Ordet som tillhör kortet"""
        self.value:str = value
        self.state: CardState = CardState.HIDDEN

    def set_state(self, new_state: CardState) -> None:
        """Sätter ett nytt tillstånd till kortet
            
            Ett kort som redan är matchat får inte ändras
            Args:
                new_state: Nytt tillstånd till kortet måste vara CardState
            Raises:
                GameStateError: om man försöker vända ett matchat kort,
                    Eller new_state inte är en CardState"""
        if self.state == CardState.MATCHED:
            raise GameStateError("Kan inte ändra state på ett matchat kort.")

        if not isinstance(new_state, CardState):
            raise GameStateError("Ny state måste vara av instans CardState")

        self.state = new_state

    def __repr__(self) -> str:
        """Returnera representation av kortet. (testing)"""
        return f"Card(value={self.value!r}, state={self.state.name})"


class WordRepository:
    """Läser in och tillhandahåller ord som används i spelet."""
    def __init__(self,
                 settings: Settings,
                 base_path: str | Path | None = None,
                 filename: str | None = None,
                 encoding: str ="utf-8"
                 ) -> None:
        """Skapar en Word Repository
        
        Args:
            Settings: Inställningsobjekt som bl.a. anger standardfilnamn
            base_path: Bas-katalog där ordlistan finns
            filename: Namn på ordfilen
            encoding: Textkodning som används vid läsning (default: "utf-8")"""

        self.settings = settings
        self.base_path = Path(base_path or settings.data_dir)
        self.filename = filename or settings.words_file
        self.encoding = encoding
        self._words: list[str] | None = None

    def load_words(self) -> list[str]:
        """Läs in ordlistan från fil och returnera en lista med ord.
        Försöker också rätta till vissa vanliga mojibake-problem (Ã¥, Ã¤, Ã¶).

        Raises:
            GameError: Om ordfilen inte hittas.

        Returns:
            En lista med strängar, ett ord per element.
        """
        if self._words is not None:
            return self._words
        path = self.base_path / self.filename
        try:
            with path.open("r", encoding=self.encoding) as f:
                loaded_list = [line.strip() for line in f if line.strip()]
        except FileNotFoundError as e:
            raise GameError(f"Hittade inte ordlistan: {path}") from e

        mojibacke = ("Ã¥", "Ã¤", "Ã¶")
        fixed_words = []
        for s in loaded_list:
            if any(marker in s for marker in mojibacke):
                try:
                    s = s.encode("latin-1").decode("utf-8")
                    # Vissa ord i ordlistan innehåller inte ÅÄÖ utan andra tecken
                    # detta fungerar som en liten work around
                except UnicodeError:
                    pass
            fixed_words.append(s)
        self._words = fixed_words
        return self._words

    def pick_words(self, n: int, rng: RandomGen) -> list[str]:
        """Välj ut n slumpmässiga ord från ordlistan.

        Args:
            n: Antal ord som ska väljas.
            rng: Slumptalsgenerator som används vid urvalet.

        Raises:
            ValueError: Om ordlistan innehåller färre ord än n.

        Returns:
            En lista med n unika ord.
        """
        words = self.load_words()
        if len(words) < n:
            raise ValueError("Inte tillräckligt med ord i ordlistan.")
        return rng.sample(words, n)


class ScoreRepository:
    """Lagrar och läser highscores från en JSON-fil."""
    def __init__(self, settings: Settings,
                 base_path: str | Path | None = None,
                 filename: str | None = None
                 ) -> None:
        """Skapa ett ScoreRepository.

        Skapar katalogen för filen om den inte redan finns.

        Args:
            settings: Inställningsobjekt för standardfilnamn.
            base_path: Bas-katalog där score-filen ska ligga (default: settings.data_dir).
            filename: Namn på score-filen (default: settings.score_file). """
        self.settings = settings
        self.base_path = Path(base_path or settings.data_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

        filename = filename or settings.score_file
        self.path: Path = self.base_path / filename

    def load(self) -> list[dict[str, Any]]:
        """Läs in alla sparade resultat.

        Returns:
            En lista med dictar som representerar sparade resultat.
            Tom lista returneras om filen saknas eller är tom.

        Raises:
            ValueError: Om filen inte innehåller giltig JSON eller inte är en lista. """
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Score filen är korrupt: {self.path}") from e

            if not isinstance(data, list):
                raise ValueError("Score filen måste innehålla en lista")
        return data

    def append(self, entry: dict[str, Any]) -> None:
        """Lägg till ett nytt resultat i score-filen.

        Skriver först till en temporär fil och ersätter sedan den
        riktiga filen för att minska risken för korrupt data.

        Args:
            entry: En dict med information om resultatet (t.ex. moves, time, difficulty). """
        data = self.load()
        data.append(entry)

        tmp = self.path.with_suffix(".tmp")

        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.flush()

        tmp.replace(self.path)

    def top(self, difficulty: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Returnera de bästa resultaten för en viss svårighetsgrad.

        Resultaten filtreras på färdiga spel (finished=True) och sorteras
        i första hand på antal drag och i andra hand på tid.

        Args:
            difficulty: Svårighetsgrad att filtrera på.
            limit: Max antal resultat att returnera (None = alla).

        Raises:
            ValueError: Om svårighetsgraden inte är tillåten.

        Returns:
            En lista med score-poster (dictar), ev. begränsad av limit. """
        if (self.settings.allowed_difficulties and difficulty not in
            self.settings.allowed_difficulties):
            raise ValueError(f"Ogiltig svårighetsgrad: {difficulty}")

        records = [
            s for s in self.load()
            if s.get("finished") and s.get("difficulty") == difficulty]

        records.sort(key=lambda x: (x.get("moves", float("inf")),
                                    x.get("time", float("inf"))))

        if limit is None:
            return records
        return records[:limit]


# Skulle kunna vara en dataklass då den inte har några metoder
class Settings:
    """Håller ihop konfiguration för spelet (svårigheter, filnamn)."""
    def __init__(
        self,
        difficulties: dict[str, int] | None = None,
        words_file: str = "memo.txt",
        score_file: str = "score.json",
        data_dir: str | Path | None = None,
    ) -> None:
        """Skapa ett nytt Settings-objekt.

        Args:
            difficulties: Mapping från svårighetsnamn till brädstorlek (t.ex. {"easy": 4}).
            words_file: Filnamn för ordlistan.
            score_file: Filnamn för score-filen.
            data_dir: Katalog där datafiler ska sparas."""
        self.difficulties = difficulties or {"easy": 4, "medium": 6, "hard": 8}
        self.allowed_difficulties = set(self.difficulties.keys())

        self.words_file = words_file
        self.score_file = score_file
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"


class RandomGen:
    """En wrapper runt random.Random med eget seed för reproducerbara spel."""
    def __init__(self, seed: int | None = None):
        """Skapa en ny slumptalsgenerator.

        Args:
            seed: Heltal som seed (None = slumpmässigt seed)."""
        if seed is None:
            seed = random.randint(0, 1_000_000)

        self.seed: int = seed
        self.rng = random.Random(self.seed)

    def get(self, a: int = 0, b: int = 1_000_000) -> int:
        """Returnera ett slumpmässigt heltal i intervallet [a, b]."""
        return self.rng.randint(a, b)

    def shuffle(self, deck: list[str]) -> None:
        """Blanda listan deck på plats."""
        self.rng.shuffle(deck)

    def sample(self, words: list[str], n: int) -> list[str]:
        """Välj n unika element från listan words i slumpmässig ordning."""
        return self.rng.sample(words, n)


def build_deck(word_repo: WordRepository, n_pairs: int, rng: RandomGen
               ) -> list[str]:
    """Bygg en kortlek med ordpar för spelet.

    Hämtar n_pairs slumpmässiga ord från word_repo och dubblar
    varje ord så att det finns ett par av varje.

    Args:
        word_repo: WordRepository som används för att hämta ord.
        n_pairs: Antal ordpar (inte totalt antal kort).
        rng: Slumptalsgenerator som används vid urvalet av ord.

    Raises:
        ValueError: Om n_pairs inte är ett heltal ≥ 1.

    Returns:
        En lista med strängar med längden 2*n_pairs."""
    if not isinstance(n_pairs, int) or n_pairs < 1:
        raise ValueError("n_pairs måste vara ett heltal ≥ 1")

    words = word_repo.pick_words(n_pairs, rng)
    deck = [w for w in words for _ in range(2)]
    # range(2) för att skapa dubbla ord i listan
    return deck
