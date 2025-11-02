from pathlib import Path
import random
random.seed()

n = 10
filename = "memo.txt"

base_path = Path(__file__).parent
file_path = base_path / "data" / filename

with file_path.open("r", encoding="utf-8") as f:
    words = [line.strip() for line in f if line.strip()]
    fixed_words = [s.encode("latin-1").decode("utf-8") for s in words]

unique_words = sorted(set(fixed_words))
selected = random.sample(unique_words, n)

print(selected)
