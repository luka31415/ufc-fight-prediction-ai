from __future__ import annotations
import numpy as np
import pandas as pd
MIN_CONFIDENCE = 0.60
MIN_EV = 0.10
KELLY_FRACTION = 0.25
MAX_FIGHT_BANKROLL = 0.03
MAX_EVENT_BANKROLL = 0.125

def american_to_decimal(x):
    if pd.isna(x): return np.nan
    x=float(x)
    if 1 < x < 20: return x
    if x >= 100: return 1 + x/100
    if x <= -100: return 1 + 100/abs(x)
    return np.nan

def bet_math(prob, decimal_odds):
    prob=np.asarray(prob,float); odds=np.asarray(decimal_odds,float)
    ev=prob*odds-1
    b=odds-1; q=1-prob
    full=np.where(b>0,(b*prob-q)/b,0.0)
    stake=np.clip(KELLY_FRACTION*full,0,MAX_FIGHT_BANKROLL)
    qualifies=(prob>=MIN_CONFIDENCE)&(ev>=MIN_EV)&(odds>1)&(stake>0)
    return pd.DataFrame({"prob":prob,"odds":odds,"ev":ev,"stake_fraction":stake,"qualifies":qualifies})
