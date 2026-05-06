import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
import json
import os
import requests
from bs4 import BeautifulSoup

# ===================== 新增：从 FBref 拉最新赛程 =====================
def get_fixtures_from_fbref(league_code="E0"):
    """
    league_code: 对应 LEAGUES 里的缩写，比如 E0=英超, I1=意甲, F1=法甲...
    这里我们遍历所有 LEAGUES，逐个拉取
    """
    league_map = {
        "E0": "9",    # Premier League
        "E1": "10",   # Championship
        "E2": "11",   # League One
        "SP1": "12",  # La Liga
        "SP2": "17",  # Segunda Division
        "I1": "13",   # Serie A
        "I2": "18",   # Serie B
        "F1": "14",   # Ligue 1
        "F2": "23",   # Ligue 2
        "D1": "20",   # Bundesliga
        "D2": "33",   # 2. Bundesliga
        "P1": "30",   # Primeira Liga
        "N1": "28",   # Eredivisie
        "B1": "37"    # Belgian Pro League
    }
    fb_id = league_map.get(league_code)
    if not fb_id:
        return pd.DataFrame()  # 不支持的联赛返回空
    
    url = f"https://fbref.com/en/comps/{fb_id}/schedule/{league_code}-Scores-and-Fixtures"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", id=f"sched_2025-2026_{fb_id}_1")
    
    if not table:
        return pd.DataFrame()
    
    df = pd.read_html(str(table))[0]
    df = df[["Date", "Home", "Away"]].copy()
    df.columns = ["Date", "HomeTeam", "AwayTeam"]
    df["Div"] = league_code
    df["Date"] = pd.to_datetime(df["Date"])
    return df

# ===================== 新增：从 football-data 补赔率 =====================
def get_odds_from_fd(league_code, seasons=["2526", "2425", "2324"]):
    dfs = []
    for season in seasons:
        url = f"https://www.football-data.co.uk/mmz4281/{season}/{league_code}.csv"
        try:
            df = pd.read_csv(url, dtype=str, usecols=["Date", "HomeTeam", "AwayTeam", "AvgH", "AvgD", "AvgA"])
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
            df["Div"] = league_code
            dfs.append(df)
        except Exception as e:
            print(f"跳过 {url}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

LEAGUES = ["E0","E1","E2","SP1","SP2","I1","I2","F1","F2","D1","D2","P1","N1","B1"]
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

# ===================== 替换后：多站互补获取 upcoming =====================
today = datetime.now().date()
day_after = today + timedelta(days=3)

# 1. 遍历所有联赛，合并 FBref 赛程 + football-data 赔率
all_fixtures = []
for league in LEAGUES:
    # 拉最新赛程
    fb_df = get_fixtures_from_fbref(league)
    # 拉赔率历史
    odds_df = get_odds_from_fd(league)
    
    # 合并：用 Date+HomeTeam+AwayTeam+Div 匹配赔率
    merged = pd.merge(
        fb_df,
        odds_df,
        on=["Date", "HomeTeam", "AwayTeam", "Div"],
        how="left"
    )
    all_fixtures.append(merged)

# 合并所有联赛
df = pd.concat(all_fixtures, ignore_index=True)

# 2. 筛选未来3天 + 有有效赔率的比赛（和你原来逻辑完全一致）
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
