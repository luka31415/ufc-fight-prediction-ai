from ufc_ai.betting import bet_math

def test_locked_thresholds():
    x=bet_math([0.60,0.59],[2.0,2.0])
    assert bool(x.loc[0,"qualifies"])
    assert not bool(x.loc[1,"qualifies"])
