"""Live base features adapted from the archived notebook feature builder."""
from pathlib import Path
import pandas as pd


def build_live_features(root, upcoming):
    """Build 42 ordered features using only fights before each card's date."""
    if upcoming.empty:
        raise ValueError("Expected at least one matchup")
    cards = upcoming.copy()
    dates = pd.to_datetime(cards.DATE, errors="raise")
    if dates.isna().any():
        raise ValueError("Missing matchup date")
    cards["_feature_order"] = range(len(cards))
    outputs = []
    for _, group in cards.groupby(dates, sort=False):
        live, features, fighter_key = _build_for_date(Path(root), group)
        live["_feature_order"] = group["_feature_order"].to_numpy()
        outputs.append(live)
    result = pd.concat(outputs).sort_values("_feature_order").drop(columns="_feature_order")
    return result.reset_index(drop=True), features, fighter_key


def _build_for_date(ROOT, upcoming):
    # Extracted from your existing cell 122; feature formulas unchanged.
    import os
    import re
    import unicodedata
    from pathlib import Path
    import numpy as np
    import pandas as pd
    import joblib
    RANDOM_SEED = 42
    CAT_WEIGHT = 0.55
    LOG_WEIGHT = 0.45
    ELO_START = 1500.0
    ELO_K = 32.0
    
    def normalize_name(name):
        if pd.isna(name):
            return ''
        name = str(name).strip()
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        name = name.casefold()
        name = re.sub('[^a-z0-9]+', ' ', name)
        return re.sub('\\s+', ' ', name).strip()
    RAW_ALIASES = {'Jose Miguel Delgado': 'Jose Delgado', 'Michael Aswell': 'Michael Aswell Jr.', 'Michael Venom Page': 'Michael Page', 'Waldo Cortes Acosta': 'Waldo Cortes-Acosta', 'Muhammadjon Naimov': 'Muhammad Naimov', 'Doo Ho Choi': 'Dooho Choi', 'Rongzhu': 'Rong Zhu', 'Joo Sang Yoo': 'JooSang Yoo', 'Osman Diaz': 'Ozzy Diaz', 'Weili Zhang': 'Zhang Weili', 'Cris Cyborg': 'Cristiane Justino', 'Ariane Lipski': 'Ariane da Silva', 'Lupita Godinez': 'Loopy Godinez', 'Josh Quinland': 'Josh Quinlan', 'Zhang Minyang': 'Zhang Mingyang', 'Zachary Reese': 'Zach Reese', 'Serghei Spivak': 'Serghei Spivac', 'Wuliji Buren': 'Wulijiburen', 'Bernardo Sopaj': 'Benardo Sopaj', 'Brianna Van Buren': 'Brianna Fortino'}
    ALIASES = {normalize_name(k): normalize_name(v) for k, v in RAW_ALIASES.items()}
    
    def fighter_key(name):
        key = normalize_name(name)
        return ALIASES.get(key, key)
    bio_candidates = [Path(str(ROOT / 'data/ufc_fighter_tott.csv')), Path(str(ROOT / 'scrape_ufc_stats/ufc_fighter_tott.csv')), Path(str(ROOT / 'scrape_ufc_stats/data/ufc_fighter_tott.csv'))]
    bio_path = None
    for candidate in bio_candidates:
        if candidate.exists():
            bio_path = candidate
            break
    if bio_path is None:
        matches = list(Path(ROOT).rglob('ufc_fighter_tott.csv'))
        if matches:
            bio_path = matches[0]
    if bio_path is None:
        raise FileNotFoundError('Could not find ufc_fighter_tott.csv')
    training = pd.read_csv(str(ROOT / 'data/training_data_with_sos.csv'), parse_dates=['DATE'])
    history = pd.read_csv(str(ROOT / 'data/fighter_history.csv'), parse_dates=['DATE'])
    results = pd.read_csv(str(ROOT / 'data/fight_results_clean.csv'), parse_dates=['DATE'])
    bio = pd.read_csv(bio_path)
    cutoff = pd.to_datetime(upcoming.DATE, errors="raise").iloc[0]
    history = history.loc[history.DATE < cutoff]
    results = results.loc[results.DATE < cutoff]
    features = [c for c in training.columns if c.startswith('DIFF_')]
    if len(features) != 42:
        raise ValueError(f'Expected 42 DIFF features, found {len(features)}')
    BASE_FEATURES = [c.replace('DIFF_', '', 1) for c in features]
    
    def canonical_col(name):
        return re.sub('[^A-Z0-9]', '', str(name).upper())
    
    def find_column(df, candidates, required=False):
        lookup = {canonical_col(c): c for c in df.columns}
        for candidate in candidates:
            key = canonical_col(candidate)
            if key in lookup:
                return lookup[key]
        if required:
            raise KeyError('Could not find any of these columns: ' + str(candidates) + '\n\nAvailable columns:\n' + str(list(df.columns)))
        return None
    fighter_col = find_column(history, ['FIGHTER'], required=True)
    opponent_col = find_column(history, ['OPPONENT', 'OPP'], required=True)
    stat_candidates = {'KD': ['KD'], 'SIG_STR_LANDED': ['SIG_STR_LANDED', 'SIG.STR._LANDED', 'SIG STR LANDED'], 'SIG_STR_ATT': ['SIG_STR_ATT', 'SIG.STR._ATT', 'SIG STR ATT'], 'TOTAL_STR_LANDED': ['TOTAL_STR_LANDED', 'TOTAL.STR._LANDED', 'TOTAL STR LANDED'], 'TOTAL_STR_ATT': ['TOTAL_STR_ATT', 'TOTAL.STR._ATT', 'TOTAL STR ATT'], 'TD_LANDED': ['TD_LANDED', 'TD_L', 'TAKEDOWN_LANDED'], 'TD_ATT': ['TD_ATT', 'TD_A', 'TAKEDOWN_ATT'], 'SUB_ATT': ['SUB_ATT', 'SUB.ATT', 'SUB_ATTEMPTS'], 'CTRL_SECONDS': ['CTRL_SECONDS', 'CONTROL_SECONDS', 'CTRL_SEC']}
    stat_cols = {}
    for output_name, candidates in stat_candidates.items():
        stat_cols[output_name] = find_column(history, candidates, required=True)
    h = pd.DataFrame()
    h['DATE'] = pd.to_datetime(history['DATE'])
    h['FIGHTER'] = history[fighter_col].astype(str)
    h['OPPONENT'] = history[opponent_col].astype(str)
    h['FIGHTER_KEY'] = h['FIGHTER'].map(fighter_key)
    h['OPP_KEY'] = h['OPPONENT'].map(fighter_key)
    for output_name, source_col in stat_cols.items():
        h[output_name] = pd.to_numeric(history[source_col], errors='coerce')
    results['FIGHTER_A_KEY'] = results['FIGHTER_A'].map(fighter_key)
    results['FIGHTER_B_KEY'] = results['FIGHTER_B'].map(fighter_key)
    results['WINNER_KEY'] = results['WINNER'].map(fighter_key) if 'WINNER' in results.columns else ''
    
    def matchup_key(date, fighter_a, fighter_b):
        names = sorted([fighter_key(fighter_a), fighter_key(fighter_b)])
        return str(pd.Timestamp(date).date()) + '||' + names[0] + '||' + names[1]
    results['MATCH_KEY'] = [matchup_key(d, a, b) for d, a, b in zip(results['DATE'], results['FIGHTER_A'], results['FIGHTER_B'])]
    h['MATCH_KEY'] = [matchup_key(d, f, o) for d, f, o in zip(h['DATE'], h['FIGHTER'], h['OPPONENT'])]
    
    def parse_clock(value):
        if pd.isna(value):
            return np.nan
        text = str(value).strip()
        match = re.match('^(\\d+):(\\d+)$', text)
        if not match:
            return np.nan
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return minutes * 60 + seconds
    results['ROUND_NUM'] = pd.to_numeric(results['ROUND'], errors='coerce')
    results['ROUND_TIME_SECONDS'] = results['TIME'].map(parse_clock)
    results['DURATION_SECONDS'] = (results['ROUND_NUM'] - 1) * 300 + results['ROUND_TIME_SECONDS']
    result_lookup = results[['MATCH_KEY', 'WINNER_KEY', 'DURATION_SECONDS']].drop_duplicates('MATCH_KEY', keep='last').set_index('MATCH_KEY')
    h['WINNER_KEY'] = h['MATCH_KEY'].map(result_lookup['WINNER_KEY'])
    h['DURATION_SECONDS'] = h['MATCH_KEY'].map(result_lookup['DURATION_SECONDS'])
    h['WIN'] = np.where(h['WINNER_KEY'] == '', np.nan, np.where(h['FIGHTER_KEY'] == h['WINNER_KEY'], 1.0, 0.0))
    missing_winner = h['WINNER_KEY'].isna() | (h['WINNER_KEY'] == '')
    h.loc[missing_winner, 'WIN'] = np.nan
    opp_stats = h[['MATCH_KEY', 'FIGHTER_KEY', 'SIG_STR_LANDED', 'SIG_STR_ATT', 'TD_LANDED', 'TD_ATT', 'CTRL_SECONDS']].copy()
    opp_stats = opp_stats.rename(columns={'FIGHTER_KEY': 'OPP_LOOKUP_KEY', 'SIG_STR_LANDED': 'OPP_SIG_STR_LANDED', 'SIG_STR_ATT': 'OPP_SIG_STR_ATT', 'TD_LANDED': 'OPP_TD_LANDED', 'TD_ATT': 'OPP_TD_ATT', 'CTRL_SECONDS': 'OPP_CTRL_SECONDS'})
    h = h.merge(opp_stats, left_on=['MATCH_KEY', 'OPP_KEY'], right_on=['MATCH_KEY', 'OPP_LOOKUP_KEY'], how='left')
    h = h.drop(columns=['OPP_LOOKUP_KEY'])
    elo_current = {}
    pre_elo = {}
    
    def get_elo(key):
        return elo_current.get(key, ELO_START)
    results_sorted = results.sort_values('DATE', kind='stable').copy()
    for _, row in results_sorted.iterrows():
        a = row['FIGHTER_A_KEY']
        b = row['FIGHTER_B_KEY']
        winner = row['WINNER_KEY']
        match = row['MATCH_KEY']
        if not a or not b:
            continue
        ra = get_elo(a)
        rb = get_elo(b)
        pre_elo[match, a] = ra
        pre_elo[match, b] = rb
        if not winner:
            continue
        expected_a = 1 / (1 + 10 ** ((rb - ra) / 400))
        if winner == a:
            score_a = 1.0
        elif winner == b:
            score_a = 0.0
        else:
            score_a = 0.5
        score_b = 1 - score_a
        expected_b = 1 - expected_a
        elo_current[a] = ra + ELO_K * (score_a - expected_a)
        elo_current[b] = rb + ELO_K * (score_b - expected_b)
    h['OPP_PRE_ELO'] = [pre_elo.get((match, opp), ELO_START) for match, opp in zip(h['MATCH_KEY'], h['OPP_KEY'])]
    bio_fighter_col = find_column(bio, ['FIGHTER'], required=True)
    dob_col = find_column(bio, ['DOB'], required=True)
    height_col = find_column(bio, ['HEIGHT'], required=True)
    reach_col = find_column(bio, ['REACH'], required=True)
    bio['FIGHTER_KEY'] = bio[bio_fighter_col].map(fighter_key)
    bio['DOB_PARSED'] = pd.to_datetime(bio[dob_col], errors='coerce')
    
    def parse_height(value):
        if pd.isna(value):
            return np.nan
        text = str(value).strip()
        try:
            x = float(text)
            if x > 40:
                return x
        except:
            pass
        match = re.search("(\\d+)\\s*['′]\\s*(\\d+)", text)
        if match:
            feet = int(match.group(1))
            inches = int(match.group(2))
            return feet * 12 + inches
        return np.nan
    
    def parse_reach(value):
        if pd.isna(value):
            return np.nan
        text = str(value).strip()
        number = re.search('(\\d+(?:\\.\\d+)?)', text)
        if not number:
            return np.nan
        return float(number.group(1))
    bio['HEIGHT_IN_PARSED'] = bio[height_col].map(parse_height)
    bio['REACH_IN_PARSED'] = bio[reach_col].map(parse_reach)
    bio_lookup = bio.drop_duplicates('FIGHTER_KEY', keep='last').set_index('FIGHTER_KEY')
    
    def safe_ratio(numerator, denominator):
        denominator = float(denominator)
        if denominator == 0 or np.isnan(denominator):
            return np.nan
        return float(numerator) / denominator
    
    def fighter_state(fighter_name, fight_date):
        key = fighter_key(fighter_name)
        past = h[(h['FIGHTER_KEY'] == key) & (h['DATE'] < fight_date)].sort_values('DATE').copy()
        n = len(past)
        wins = int((past['WIN'] == 1).sum())
        losses = int((past['WIN'] == 0).sum())
        win_pct = wins / n if n > 0 else np.nan
    
        def avg(col):
            if n == 0:
                return np.nan
            return pd.to_numeric(past[col], errors='coerce').mean()
    
        def total(col):
            if n == 0:
                return 0.0
            return pd.to_numeric(past[col], errors='coerce').sum(min_count=1)
        duration_seconds = total('DURATION_SECONDS')
        duration_minutes = duration_seconds / 60 if pd.notna(duration_seconds) else np.nan
        sig_landed = total('SIG_STR_LANDED')
        sig_att = total('SIG_STR_ATT')
        opp_sig_landed = total('OPP_SIG_STR_LANDED')
        opp_sig_att = total('OPP_SIG_STR_ATT')
        td_landed = total('TD_LANDED')
        td_att = total('TD_ATT')
        opp_td_landed = total('OPP_TD_LANDED')
        opp_td_att = total('OPP_TD_ATT')
        sub_att = total('SUB_ATT')
        ctrl = total('CTRL_SECONDS')
        opp_ctrl = total('OPP_CTRL_SECONDS')
        recent = past.tail(3).copy()
        recent_n = len(recent)
    
        def recent_total(col):
            if recent_n == 0:
                return 0.0
            return pd.to_numeric(recent[col], errors='coerce').sum(min_count=1)
        recent_duration_sec = recent_total('DURATION_SECONDS')
        recent_duration_min = recent_duration_sec / 60 if pd.notna(recent_duration_sec) else np.nan
        if n > 0:
            last_date = past['DATE'].max()
            days_since = (fight_date - last_date).days
        else:
            last_date = pd.NaT
            days_since = np.nan
        if key in bio_lookup.index:
            profile = bio_lookup.loc[key]
            if isinstance(profile, pd.DataFrame):
                profile = profile.iloc[-1]
            dob = profile['DOB_PARSED']
            height = profile['HEIGHT_IN_PARSED']
            reach = profile['REACH_IN_PARSED']
        else:
            dob = pd.NaT
            height = np.nan
            reach = np.nan
        age = (fight_date - dob).days / 365.25 if pd.notna(dob) else np.nan
        current_elo = elo_current.get(key, ELO_START)
        opp_elos = pd.to_numeric(past['OPP_PRE_ELO'], errors='coerce')
        prior_avg_opp_elo = opp_elos.mean() if n else np.nan
        prior_max_opp_elo = opp_elos.max() if n else np.nan
        recent3_avg_opp_elo = opp_elos.tail(3).mean() if n else np.nan
        r_sig_landed = recent_total('SIG_STR_LANDED')
        r_opp_sig_landed = recent_total('OPP_SIG_STR_LANDED')
        r_td_landed = recent_total('TD_LANDED')
        r_opp_td_landed = recent_total('OPP_TD_LANDED')
        r_sub_att = recent_total('SUB_ATT')
        r_ctrl = recent_total('CTRL_SECONDS')
        r_opp_ctrl = recent_total('OPP_CTRL_SECONDS')
        recent_win_rate = (recent['WIN'] == 1).sum() / recent_n if recent_n else np.nan
        state = {'PRIOR_FIGHTS': float(n), 'PRIOR_WINS': float(wins), 'PRIOR_LOSSES': float(losses), 'PRIOR_WIN_PCT': win_pct, 'PRIOR_AVG_KD': avg('KD'), 'PRIOR_AVG_SIG_STR_LANDED': avg('SIG_STR_LANDED'), 'PRIOR_AVG_SIG_STR_ATT': avg('SIG_STR_ATT'), 'PRIOR_AVG_TOTAL_STR_LANDED': avg('TOTAL_STR_LANDED'), 'PRIOR_AVG_TOTAL_STR_ATT': avg('TOTAL_STR_ATT'), 'PRIOR_AVG_TD_LANDED': avg('TD_LANDED'), 'PRIOR_AVG_TD_ATT': avg('TD_ATT'), 'PRIOR_AVG_SUB.ATT': avg('SUB_ATT'), 'PRIOR_AVG_CTRL_SECONDS': avg('CTRL_SECONDS'), 'PRIOR_SIG_STR_ACC': safe_ratio(sig_landed, sig_att), 'PRIOR_TD_ACC': safe_ratio(td_landed, td_att), 'DAYS_SINCE_LAST_FIGHT': days_since, 'ELO': current_elo, 'UFC_DEBUT': float(n == 0), 'AGE': age, 'HEIGHT_IN': height, 'REACH_IN': reach, 'RATE_SIG_STR_LANDED_PM': safe_ratio(sig_landed, duration_minutes), 'RATE_SIG_STR_ABSORBED_PM': safe_ratio(opp_sig_landed, duration_minutes), 'RATE_TD_LANDED_PER15': safe_ratio(td_landed, duration_minutes) * 15 if duration_minutes else np.nan, 'RATE_TD_ALLOWED_PER15': safe_ratio(opp_td_landed, duration_minutes) * 15 if duration_minutes else np.nan, 'RATE_SUB_ATT_PER15': safe_ratio(sub_att, duration_minutes) * 15 if duration_minutes else np.nan, 'RATE_SIG_STR_ACC': safe_ratio(sig_landed, sig_att), 'RATE_SIG_STR_DEF': 1 - safe_ratio(opp_sig_landed, opp_sig_att) if pd.notna(safe_ratio(opp_sig_landed, opp_sig_att)) else np.nan, 'RATE_TD_ACC': safe_ratio(td_landed, td_att), 'RATE_TD_DEF': 1 - safe_ratio(opp_td_landed, opp_td_att) if pd.notna(safe_ratio(opp_td_landed, opp_td_att)) else np.nan, 'RATE_CTRL_SHARE': safe_ratio(ctrl, ctrl + opp_ctrl), 'RECENT3_SIG_LANDED_PM': safe_ratio(r_sig_landed, recent_duration_min), 'RECENT3_SIG_ABSORBED_PM': safe_ratio(r_opp_sig_landed, recent_duration_min), 'RECENT3_TD_LANDED_PER15': safe_ratio(r_td_landed, recent_duration_min) * 15 if recent_duration_min else np.nan, 'RECENT3_TD_ALLOWED_PER15': safe_ratio(r_opp_td_landed, recent_duration_min) * 15 if recent_duration_min else np.nan, 'RECENT3_SUB_ATT_PER15': safe_ratio(r_sub_att, recent_duration_min) * 15 if recent_duration_min else np.nan, 'RECENT3_CTRL_SHARE': safe_ratio(r_ctrl, r_ctrl + r_opp_ctrl), 'RECENT3_WIN_RATE': recent_win_rate, 'RECENT3_FIGHT_COUNT': float(recent_n), 'PRIOR_AVG_OPP_ELO': prior_avg_opp_elo, 'PRIOR_MAX_OPP_ELO': prior_max_opp_elo, 'RECENT3_AVG_OPP_ELO': recent3_avg_opp_elo}
        return (state, {'KEY': key, 'UFC_FIGHTS': n, 'LAST_FIGHT': last_date, 'BIO_FOUND': key in bio_lookup.index})
    live_rows = []
    for _, fight in upcoming.iterrows():
        date = pd.Timestamp(fight['DATE'])
        fighter_a = fight['FIGHTER_A']
        fighter_b = fight['FIGHTER_B']
        state_a, info_a = fighter_state(fighter_a, date)
        state_b, info_b = fighter_state(fighter_b, date)
        row = {'DATE': date, 'EVENT': fight['EVENT'], 'FIGHTER_A': fighter_a, 'FIGHTER_B': fighter_b, 'A_UFC_FIGHTS': info_a['UFC_FIGHTS'], 'B_UFC_FIGHTS': info_b['UFC_FIGHTS'], 'A_LAST_FIGHT': info_a['LAST_FIGHT'], 'B_LAST_FIGHT': info_b['LAST_FIGHT'], 'A_BIO_FOUND': info_a['BIO_FOUND'], 'B_BIO_FOUND': info_b['BIO_FOUND']}
        for base in BASE_FEATURES:
            a = state_a.get(base, np.nan)
            b = state_b.get(base, np.nan)
            try:
                diff = float(a) - float(b)
            except:
                diff = np.nan
            row['DIFF_' + base] = diff
        live_rows.append(row)
    live = pd.DataFrame(live_rows)
    missing_features = [c for c in features if c not in live.columns]
    if missing_features:
        raise ValueError('Missing live features: ' + str(missing_features))
    live[features] = live[features].replace([np.inf, -np.inf], np.nan)
    
    def quality_label(row):
        a = int(row['A_UFC_FIGHTS'])
        b = int(row['B_UFC_FIGHTS'])
        if a == 0 or b == 0:
            return 'DEBUT / OUTSIDE-UFC DATA WARNING'
        if a <= 2 or b <= 2:
            return 'VERY LOW UFC DATA'
        if a <= 4 or b <= 4:
            return 'LOW UFC DATA'
        return 'NORMAL'
    live['DATA_QUALITY'] = live.apply(quality_label, axis=1)
    return live, features, fighter_key
