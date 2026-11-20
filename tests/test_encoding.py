"""Files must be read and written as UTF-8 on every computer.

Windows uses an old default encoding (cp1252) that can't store many letters,
e.g. Japanese titles or names like 'Zoë'. If any read/write forgets to say
encoding="utf-8", it works on Mac/Linux and crashes on Windows. These tests
catch that before employee A does.
"""
import re
from pathlib import Path

import pandas as pd

from streamvault.fetch import save_payload
from streamvault.shape import load_payloads

ROOT = Path(__file__).resolve().parents[1]


def test_non_latin_text_round_trips(tmp_path):
    payload = {"id": 1, "title": "千と千尋の神隠し", "overview": "Zoë – “quotes” – ☆"}
    save_payload(tmp_path, 1, payload)
    assert load_payloads(tmp_path, pd.Series([1]))[0] == payload


def test_every_text_read_and_write_names_utf8():
    files = [*ROOT.glob("src/**/*.py"), *ROOT.glob("scripts/*.py"), ROOT / "run.py"]
    pattern = re.compile(r"\.(read_text|write_text)\(")
    missing = []
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line) and "encoding=" not in line:
                # allow the call to finish on the next lines (multi-line calls)
                rest = "".join(f.read_text(encoding="utf-8").splitlines()[n - 1:n + 3])
                if "encoding=" not in rest:
                    missing.append(f"{f.relative_to(ROOT)}:{n}")
    assert not missing, f"read_text/write_text without encoding: {missing}"
