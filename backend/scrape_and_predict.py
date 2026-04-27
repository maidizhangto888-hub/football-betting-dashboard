import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
import json
import os

# ========================= CONFIG =========================
LEAGUES = ["E0","E1","E2","E3","EC","SP1","SP2","I1","I2","F1","F2","D1","D2","P1","N1","B1","G1","T1","SC0","SC1","SC2","SC3"]
MIN_EDGE = 0.05
# =======================================================

print("Fetching fixtures and building xG-style model...")

# 1. Get historical results for strength calculation (last ~2 seasons where possible)
historical_urls = [
    "https://www.football-data.co.uk/mmz4281/2425/E0.csv",  # Example: adjust seasons as needed
    "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
    # Add more leagues/seasons if you want (we'll start simple with E0 and expand later)
]

hist_dfs = []
for url in historical_urls:
    try:
        df_hist = pd.read_csv(url)
        hist_dfs.append(df_hist)
    except:
        pass

if hist_dfs:
    historical = pd.concat(hist_dfs, ignore_index=True)
    print(f"Loaded {len(historical)} historical matches for strength calculation.")
else:
    historical = pd.DataFrame()
    print("Using default strengths (no historical data loaded).")

# Calculate league/team attack/defense strengths (simple xG-style)
if not historical.empty:
    # Basic attack/defense
    historical['HomeGoals'] = pd.to_numeric(historical.get('FTHG', 0), errors='coerce')
    historical['AwayGoals'] = pd.to_numeric(historical.get('FTAG', 0), errors='coerce')
    
    avg_home_goals = historical['HomeGoals'].mean() or 1.48
    avg_away_goals = historical['AwayGoals'].mean() or 1.22
    
    # Simple team strengths (can be expanded with more leagues)
    team_stats = {}
    # For now, fallback to league averages if historical is limited
else:
    avg_home_goals = 1.48
    avg_away_goals = 1.22

print(f"Using avg home xG: {avg_home_goals:.2f}, avg away xG: {avg_away_goals:.2f}")

# 2. Get upcoming fixtures
url = "https://www.football-data.co.uk/fixtures.csv"
df = pd.read_csv(url, dtype=str)

df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')
today = datetime.now().date()
day_after = today + timedelta(days=2)

upcoming = df[
    (df['Div'].isin(LEAGUES)) & 
    (df['Date'].dt.date >= today) & 
    (df['Date'].dt.date <= day_after) &
    (pd.to_numeric(df.get('AvgH', 0), errors='coerce') > 1.0)
].copy()

print(f"Found {len(upcoming)} upcoming matches.")

results = []
for _, row in upcoming.iterrows():
    home_odds = float(row.get('AvgH', 2.0) or 2.0)
    draw_odds = float(row.get('AvgD', 3.5) or 3.5)
    away_odds = float(row.get('AvgA', 3.0) or 3.0)

    # xG-style expected goals (home advantage built in)
    home_xg = avg_home_goals * 1.1   # slight home boost
    away_xg = avg_away_goals

    # Poisson probabilities
    max_goals = 6
    home_probs = [poisson.pmf(i, home_xg) for i in range(max_goals + 1)]
    away_probs = [poisson.pmf(i, away_xg) for i in range(max_goals + 1)]

    home_win = draw = away_win = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob = home_probs[h] * away_probs[a]
            if h > a:
                home_win += prob
            elif h == a:
                draw += prob
            else:
                away_win += prob

    total = home_win + draw + away_win
    if total > 0:
        home_win /= total
        draw /= total
        away_win /= total

    # Value detection
    imp_home = 1 / home_odds if home_odds > 1 else 0
    imp_draw = 1 / draw_odds if draw_odds > 1 else 0
    imp_away = 1 / away_odds if away_odds > 1 else 0

    value_home = home_win - imp_home if home_win > imp_home + MIN_EDGE else 0
    value_draw = draw - imp_draw if draw > imp_draw + MIN_EDGE else 0
    value_away = away_win - imp_away if away_win > imp_away + MIN_EDGE else 0

    # Over 2.5 probability
    over_25 = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            if h + a > 2.5:
                over_25 += home_probs[h] * away_probs[a]
    over_25 /= total if total > 0 else 1

    match = {
        "league": str(row.get('Div', 'UNK')),
        "date": row['Date'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['Date']) else "TBD",
        "home_team": str(row.get('HomeTeam', 'Unknown')),
        "away_team": str(row.get('AwayTeam', 'Unknown')),
        "home_odds": home_odds,
        "draw_odds": draw_odds,
        "away_odds": away_odds,
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "home_win_prob": round(home_win, 4),
        "draw_prob": round(draw, 4),
        "away_win_prob": round(away_win, 4),
        "over_25_prob": round(over_25, 4),
        "value_home": round(value_home, 4),
        "value_draw": round(value_draw, 4),
        "value_away": round(value_away, 4)
    }
    results.append(match)

os.makedirs("data", exist_ok=True)
with open("data/predictions.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ Saved {len(results)} matches with xG-style predictions!")
