import json
from pathlib import Path

base_path = Path(__file__).parent / "data_test"
test_dir_path = base_path

def load_score(filename="score_test.json"):
    path = test_dir_path / filename
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
       
        data = json.load(file)

    if not isinstance(data, list):
        return []
    return data

def save_score(data, filename="score_test.json"):
    path = test_dir_path / filename
    score = load_score(filename)
    score.append(data)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as file:
        json.dump(score, file)
    tmp.replace(path)


result =  {
    "ETT": "Värde_Ett",
    "TVÅ": "Värde_TVÅ",
    "TRE": "Värde_TRE",
    "FYRA": "Värde_FYRA",
}
save_score(result)


A = load_score()
print(A)