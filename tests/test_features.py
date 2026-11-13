from ufc_ai.features import PRODUCTION_FEATURES, PRODUCTION_V1_FEATURES


def test_feature_count():
    assert len(PRODUCTION_V1_FEATURES) == 42
    assert len(PRODUCTION_FEATURES) == 46
    assert len(PRODUCTION_FEATURES) == len(set(PRODUCTION_FEATURES))
    assert PRODUCTION_FEATURES[:42] == PRODUCTION_V1_FEATURES
