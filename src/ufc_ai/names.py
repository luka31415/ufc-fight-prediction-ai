import re
import unicodedata
import pandas as pd

def normalize_name(value: object) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii").casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    suffixes = {"jr", "sr", "ii", "iii", "iv"}
    return " ".join(t for t in text.split() if t not in suffixes)

def unordered_pair_key(a: object, b: object) -> str:
    return "||".join(sorted([normalize_name(a), normalize_name(b)]))
