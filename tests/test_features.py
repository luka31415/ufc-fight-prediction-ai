from ufc_ai.features import PRODUCTION_FEATURES

def test_feature_count():
    assert len(PRODUCTION_FEATURES)==42
    assert len(PRODUCTION_FEATURES)==len(set(PRODUCTION_FEATURES))
