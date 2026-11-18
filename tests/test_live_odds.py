import pandas as pd
import pytest
from ufc_ai import live_odds as odds


def quote(a="11", b="22", price=-150):
    return {"provider": {"id": "1", "name": "Fixture"},
            "homeAthleteOdds": {"athlete": {"id": b}, "moneyLine": 130},
            "awayAthleteOdds": {"athlete": {"id": a}, "moneyLine": price}}


def cards(date="2099-01-01T00:00:00Z"):
    return pd.DataFrame([dict(EVENT_ID="1", FIGHT_ID="2", FIGHTER_A="A", FIGHTER_B="B",
                             A_ESPN_ID="11", B_ESPN_ID="22", EVENT_START_UTC=date)])


def test_reversed_order_and_ref_identity():
    item = quote()
    item["homeAthleteOdds"]["athlete"] = {"$ref": "http://sports.core.api.espn.com/athletes/22"}
    assert odds.parse_quote(item, "11", "22") == (-150, 130)
    assert odds.parse_quote(item, "11", "33") is None


@pytest.mark.parametrize("price", [0, 99, float("nan"), float("inf")])
def test_invalid_moneyline(price):
    with pytest.raises(ValueError):
        odds.parse_quote(quote(price=price), "11", "22")


def test_duplicate_identity():
    with pytest.raises(ValueError):
        odds.parse_quote(quote(b="11"), "11", "22")


def test_complete_provider_and_partial_quotes(monkeypatch):
    partial = quote(b="33")
    monkeypatch.setattr(odds, "get_json", lambda url: {"items": [quote(price=0), partial, quote()]})
    result, audit = odds.fetch_odds(cards())
    assert result.iloc[0].A_ODDS == -150
    assert result.iloc[0].B_ODDS == 130
    assert audit.iloc[0].STATUS == "ODDS_FOUND"
    monkeypatch.setattr(odds, "get_json", lambda url: {"items": [partial]})
    assert odds.fetch_odds(cards())[0].empty


@pytest.mark.parametrize("date", ["2000-01-01T00:00:00Z", "invalid", None])
def test_closed_or_missing_start_avoids_request(monkeypatch, date):
    def forbidden(url):
        raise AssertionError("Unexpected network request")
    monkeypatch.setattr(odds, "get_json", forbidden)
    assert odds.fetch_odds(cards(date))[0].empty


def test_duplicate_cards():
    with pytest.raises(ValueError, match="Duplicate"):
        odds.fetch_odds(pd.concat([cards(), cards()]))
