import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
import json
import os

LEAGUES = ["E0","E1","E2","SP1","SP2","I1","F1","F2","D1","D2","P1","N1","SWE","JPN","FIN","NOR","MLS"]
MIN_EDGE = 0.05

print("Loading extensive historical data for rich H2H...")

historical_urls = []
# 修改为近3个赛季：23/24, 24/25, 25/26
seasons = ["2526", "2425", "2324"]

for league in LEAGUES:
    for season in seasons:
        # 动态生成所有联赛、最近3个赛季的下载链接
        url = f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
        historical_urls.append(url)

hist_dfs = []
for url in historical_urls:
    try:
        df = pd.read_csv(url, dtype=str)
        df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')
        hist_dfs.append(df)
        print(f"Loaded {len(df)} matches from {url}")
    except Exception as e:
        print(f"Failed {url}: {e}")

historical = pd.concat(hist_dfs, ignore_index=True) if hist_dfs else pd.DataFrame()
print(f"Total historical matches: {len(historical)}")

# Upcoming
url = "https://www.football-data.co.uk/fixtures.csv"
df = pd.read_csv(url, dtype=str)
df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')

today = datetime.now().date()
day_after = today + timedelta(days=3)

upcoming = df[
    (df['Div'].isin(LEAGUES)) & 
    (df['Date'].dt.date >= today) & 
    (df['Date'].dt.date <= day_after) &
    (pd.to_numeric(df.get('AvgH', 0), errors='coerce') > 1)
].copy()

print(f"Found {len(upcoming)} upcoming matches.")

results = []
for _, row in upcoming.iterrows():
    league = str(row.get('Div', 'UNK'))
    home_team = str(row.get('HomeTeam', 'Unknown'))
    away_team = str(row.get('AwayTeam', 'Unknown'))
    date_str = row['Date'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['Date']) else "TBD"

    home_odds = float(row.get('AvgH', 2.5) or 2.5)
    draw_odds = float(row.get('AvgD', 3.4) or 3.4)
    away_odds = float(row.get('AvgA', 3.0) or 3.0)

    home_xg = round(1.55 + np.random.normal(0, 0.2), 2)
    away_xg = round(1.28 + np.random.normal(0, 0.18), 2)

    max_goals = 6
    home_probs = [poisson.pmf(i, home_xg) for i in range(max_goals + 1)]
    away_probs = [poisson.pmf(i, away_xg) for i in range(max_goals + 1)]
    home_win = draw = away_win = over_25 = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = home_probs[h] * away_probs[a]
            if h > a: home_win += p
            elif h == a: draw += p
            else: away_win += p
            if h + a > 2.5: over_25 += p
    total = home_win + draw + away_win or 1
    home_win /= total
    draw /= total
    away_win /= total
    over_25 /= total

    value_home = home_win - (1/home_odds) if home_win > (1/home_odds) + MIN_EDGE else 0
    value_draw = draw - (1/draw_odds) if draw > (1/draw_odds) + MIN_EDGE else 0
    value_away = away_win - (1/away_odds) if away_win > (1/away_odds) + MIN_EDGE else 0

    details = {"h2h": [], "home_form": [], "away_form": []}
    if not historical.empty:
        h2h_df = historical[
            ((historical['HomeTeam'] == home_team) & (historical['AwayTeam'] == away_team)) |
            ((historical['HomeTeam'] == away_team) & (historical['AwayTeam'] == home_team))
        ].sort_values('Date', ascending=False).head(8)
        for _, m in h2h_df.iterrows():
            details["h2h"].append({
                "date": m['Date'].strftime('%Y-%m-%d') if pd.notna(m['Date']) else "",
                "home": str(m.get('HomeTeam', '')),
                "away": str(m.get('AwayTeam', '')),
                "score": f"{m.get('FTHG', '?')}–{m.get('FTAG', '?')}"
            })

        home_form_df = historical[historical['HomeTeam'] == home_team].sort_values('Date', ascending=False).head(6)
        for _, m in home_form_df.iterrows():
            details["home_form"].append({
                "opponent": str(m.get('AwayTeam', '')),
                "score": f"{m.get('FTHG', '?')}–{m.get('FTAG', '?')}"
            })

        away_form_df = historical[historical['AwayTeam'] == away_team].sort_values('Date', ascending=False).head(6)
        for _, m in away_form_df.iterrows():
            details["away_form"].append({
                "opponent": str(m.get('HomeTeam', '')),
                "score": f"{m.get('FTHG', '?')}–{m.get('FTAG', '?')}"
            })

    match = {
        "league": league,
        "date": date_str,
        "home_team": home_team,
        "away_team": away_team,
        "home_odds": home_odds,
        "draw_odds": draw_odds,
        "away_odds": away_odds,
        "home_xg": home_xg,
        "away_xg": away_xg,
        "home_win_prob": round(home_win, 4),
        "draw_prob": round(draw, 4),
        "away_win_prob": round(away_win, 4),
        "over_25_prob": round(over_25, 4),
        "value_home": round(value_home, 4),
        "value_draw": round(value_draw, 4),
        "value_away": round(value_away, 4),
        "details": details
    }
    results.append(match)

os.makedirs("frontend/data", exist_ok=True)
with open("frontend/data/predictions.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ Saved {len(results)} matches with multi-season H2H data!")
