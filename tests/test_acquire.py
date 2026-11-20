"""Ledger outcomes after fetching, tested offline with a fake fetch result."""
from pathlib import Path

import pandas as pd

from streamvault.acquire import outcome_ledger
from streamvault.ids import build_id_ledger

FIXTURES = Path(__file__).parent / "fixtures"


def test_outcomes_reconcile_and_join_does_not_duplicate():
    ledger = build_id_ledger(FIXTURES / "id_list_messy.csv")   # ids 155 (x2) and 278 valid
    fetched = pd.DataFrame({"tmdb_id": [155, 278], "http_status": [200, 404],
                            "from_cache": [False, False], "error": [None, "not found"],
                            "returned_id": [155, None]})
    out = outcome_ledger(ledger, fetched)
    assert len(out) == len(ledger)                         # join neither drops nor adds lines
    assert out["outcome"].tolist() == ["fetched", "not_found_on_tmdb", "blank_line",
                                       "invalid_format", "invalid_imdb_id", "invalid_format",
                                       "duplicate", "invalid_format"]
    assert out.loc[out["outcome"] == "duplicate", "http_status"].isna().all()
    assert not out["id_mismatch"].any()
