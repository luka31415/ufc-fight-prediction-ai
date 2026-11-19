from copy import deepcopy
from pathlib import Path
import runpy
import pandas as pd
import pytest

ns = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/settle_picks.py'))
settle, summarize = ns['settle'], ns['summarize']


def snapshot():
    return pd.DataFrame([dict(EVENT_ID='01', FIGHT_ID='02', A_ESPN_ID='03', B_ESPN_ID='04',
        DATE='2026-11-01', EVENT='Card', FIGHTER_A='A', FIGHTER_B='B', P_A=.7,
        PICK_ODDS_DECIMAL=2.5, SIM_STAKE=50.)])


def events(completed=True, winner='03', description='Final'):
    return [dict(id='01', competitions=[dict(id='02', status={'type': {'completed': completed,
        'description': description}}, competitors=[dict(id=i, winner=i == winner) for i in ['04', '03']])])]


@pytest.mark.parametrize('winner,flat,strategy', [('03', 150., 75.), ('04', -100., -50.)])
def test_id_matching_and_idempotence(winner, flat, strategy):
    original = snapshot()
    result = settle(original, events(winner=winner))
    assert result.loc[0, 'FLAT_PNL'] == flat
    assert result.loc[0, 'STRATEGY_PNL'] == strategy
    pd.testing.assert_frame_equal(settle(result, events(winner=winner)), result)
    assert 'RESULT_STATUS' not in original


@pytest.mark.parametrize('description', ['Canceled', 'Cancelled', 'Draw', 'No Contest', 'No-Contest'])
def test_void(description):
    result = settle(snapshot(), events(description=description, winner=None))
    assert result.loc[0, 'RESULT_STATUS'] == 'VOID'
    assert result.loc[0, 'FLAT_PNL'] == result.loc[0, 'STRATEGY_PNL'] == 0
    summary = summarize(result, 100.).iloc[0]
    assert summary.VOID == 1 and summary.FLAT_BETS == summary.STRATEGY_BETS == 0


@pytest.mark.parametrize('response,status', [([], 'RESULT_NOT_FOUND'),
    (events(completed=False), 'PENDING'), (events(winner=None), 'COMPLETED_WITHOUT_WINNER_REVIEW')])
def test_unresolved_not_losses(response, status):
    result = settle(snapshot(), response)
    assert result.loc[0, 'RESULT_STATUS'] == status and pd.isna(result.loc[0, 'FLAT_PNL'])
    assert summarize(result, 100.).iloc[0].UNRESOLVED == 1


def test_changed_or_missing_matchup_and_duplicate_results():
    response = events()
    response[0]['competitions'][0]['competitors'][0]['id'] = '999'
    assert settle(snapshot(), response).loc[0, 'RESULT_STATUS'] == 'MATCHUP_CHANGED_REVIEW'
    response[0]['competitions'][0]['competitors'] = []
    assert settle(snapshot(), response).loc[0, 'RESULT_STATUS'] == 'MATCHUP_CHANGED_REVIEW'
    with pytest.raises(ValueError, match='Duplicate result'):
        settle(snapshot(), events() + events())
    with pytest.raises(ValueError, match='Duplicate snapshot'):
        settle(pd.concat([snapshot(), snapshot()]), events())


def test_absent_odds_not_zero_profit_bet():
    frame = snapshot()
    frame['PICK_ODDS_DECIMAL'] = float('nan')
    frame['SIM_STAKE'] = 0.
    result = settle(frame, events())
    assert pd.isna(result.loc[0, 'FLAT_PNL']) and result.loc[0, 'STRATEGY_PNL'] == 0
    summary = summarize(result, 100.).iloc[0]
    assert summary.SETTLED_WITHOUT_ODDS == 1 and pd.isna(summary.FLAT_NET_PNL)
    frame['SIM_STAKE'] = 10.
    with pytest.raises(ValueError, match='without saved odds'):
        settle(frame, events())


@pytest.mark.parametrize('column,value', [('P_A', float('nan')), ('P_A', 1.1),
    ('SIM_STAKE', -1), ('SIM_STAKE', float('inf')), ('PICK_ODDS_DECIMAL', 1), ('A_ESPN_ID', None)])
def test_invalid_input(column, value):
    frame = snapshot()
    frame[column] = value
    with pytest.raises(ValueError):
        settle(frame, events())


def test_offline_cli_preserves_snapshot(tmp_path):
    import json
    path = tmp_path / 'predictions_v21.csv'
    snapshot().to_csv(path, index=False)
    before = path.read_bytes()
    fixture = tmp_path / 'events.json'
    fixture.write_text(json.dumps({'events': events()}))
    ns['main'](['--predictions', str(path), '--events-json', str(fixture)])
    assert path.read_bytes() == before
    ledgers = list(tmp_path.glob('settlement_*/fight_ledger.csv'))
    assert len(ledgers) == 1
    assert pd.read_csv(ledgers[0]).loc[0, 'FLAT_PNL'] == 150.


def test_incidental_draw_substring_is_not_void():
    result = settle(snapshot(), events(description='Withdrawn', winner=None))
    assert result.loc[0, 'RESULT_STATUS'] == 'COMPLETED_WITHOUT_WINNER_REVIEW'
