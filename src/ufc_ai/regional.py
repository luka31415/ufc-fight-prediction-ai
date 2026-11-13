"""Experimental V2.1 regional feature; does not change production V2."""
import re
import unicodedata

import pandas as pd

FEATURE_NAME = "DIFF_UAE_RUSSIA_HOME"


def _norm(value):
    if pd.isna(value):
        return ""
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def normalize_country(value):
    value = _norm(value)
    return {"russian federation": "russia", "uae": "united arab emirates",
            "u a e": "united arab emirates"}.get(value, value)


def is_uae_location(value):
    value = _norm(value)
    return any(re.search(r"\b" + marker + r"\b", value) for marker in
               ("united arab emirates", "uae", "u a e", "abu dhabi", "yas island", "dubai"))


def _event_flag(value):
    if pd.isna(value):
        raise ValueError("UAE event flag is missing")
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
        raise ValueError("UAE event flag must be boolean or 0/1")
    if value in (True, False):
        return bool(value)
    raise ValueError("UAE event flag must be boolean or 0/1")


def calculate_uae_russia_feature(fighter_a_country, fighter_b_country,
                               is_uae_event=None, event_location=None):
    """Return A-minus-B Russia indicator at an explicitly located UAE event.

    Unknown countries at UAE events are rejected to avoid treating missing
    country data as verified non-Russian nationality.
    """
    if is_uae_event is None:
        if not _norm(event_location):
            raise ValueError("Provide an event location or explicit UAE flag")
        flag = is_uae_location(event_location)
    else:
        flag = _event_flag(is_uae_event)
    if not flag:
        return 0.0
    a, b = normalize_country(fighter_a_country), normalize_country(fighter_b_country)
    if not a or not b:
        raise ValueError("Both fighter countries are required for UAE events")
    return float(int(a == "russia") - int(b == "russia"))


def add_feature(frame, a_country_col="A_COUNTRY", b_country_col="B_COUNTRY",
                is_uae_col=None, event_location_col=None):
    """Return a copy with the regional feature, preserving row order/index."""
    if is_uae_col is None and event_location_col is None:
        raise ValueError("Need is_uae_col or event_location_col")
    out = frame.copy()
    out[FEATURE_NAME] = [calculate_uae_russia_feature(
        row[a_country_col], row[b_country_col],
        is_uae_event=row[is_uae_col] if is_uae_col is not None else None,
        event_location=row[event_location_col] if event_location_col is not None else None,
    ) for _, row in out.iterrows()]
    return out
