from pathlib import Path
import random
import json


class DataLoader:
    def __init__(self, base_path=None):
        self.base_path = Path(base_path or Path(__file__).parent.parent) / "data"
        self.score_path = self.base_path

    def load_words(self, filename="memo.txt"):
        path = self.base_path / filename
        with path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            words = [s.encode("latin-1").decode("utf-8") for s in lines]
        return sorted(set(words))

    def pick_words(self, n, rng=None):
        words = self.load_words()
        if rng is None:
            rng = random
        return rng.sample(words, n)

    def load_score(self, filename="score.json"):
        path = self.score_path / filename
        if not path.exists:
            return []
        with path.open("r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print("fel format")
                return []

        if not isinstance(data, list):
            return []
        return data

    def save_score(self, result, filename="score.json"):
        path = self.score_path / filename
        score = self.load_score()
        score.append(result)
        with path.open("w", encoding="utf-8") as file:
            json.dump(score, file, indent=4, ensure_ascii=False)
