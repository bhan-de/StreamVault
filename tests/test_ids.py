"""The id ledger must account for every line, whatever the file throws at it."""
from pathlib import Path

import pytest

from streamvault.ids import (BLANK, DUPLICATE, IMDB_ID, INVALID, TO_FETCH,
                             build_id_ledger, reconcile)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def ledger():
    return build_id_ledger(FIXTURES / "id_list_messy.csv")


def test_every_line_has_a_row(ledger):
    assert len(ledger) == 8                     # 8 data lines, CRLF endings, one blank
    assert ledger["line_no"].tolist() == list(range(2, 10))


def test_statuses(ledger):
    assert ledger["status"].tolist() == [
        TO_FETCH,    # 155
        TO_FETCH,    # " 278 " (whitespace stripped)
        BLANK,       # empty line pandas would silently skip
        INVALID,     # -1
        IMDB_ID,     # tt0468569
        INVALID,     # N/A
        DUPLICATE,   # 155 again
        INVALID,     # 0155: leading zero is not a TMDb id format, flagged not guessed
    ]


def test_duplicate_points_to_first_occurrence(ledger):
    dup = ledger.loc[ledger["status"] == DUPLICATE].iloc[0]
    assert dup["duplicate_of_line"] == 2


def test_reconcile_sums_and_checks_expected(ledger):
    assert reconcile(ledger).sum() == 8
    with pytest.raises(AssertionError):
        reconcile(ledger, expected_lines=9)


def test_unique_ids_to_fetch_are_unique(ledger):
    to_fetch = ledger.loc[ledger["status"] == TO_FETCH, "tmdb_id"]
    assert to_fetch.is_unique
