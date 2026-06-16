import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
import json
import os

LEAGUES = ["E0", "E1", "E2", "SP1", "SP2", "I1", "F1", "F2", "D1", "D2", "P1"]
PREDICT_LEAGUES = LEAGUES + ["JPN","J1", "J1 League"]
MIN_EDGE = 0.05

print("Loading extensive historical data for rich H2H...")

# 【修复 1】必须在此处显式初始化历史 DataFrame 存储列表
hist_dfs = []
seasons = ["2526", "2425", "2324"]

# --- 1. 遍历下载并清洗欧洲五大联赛历史数据 ---
print("Loading European historical data...")
for league in LEAGUES:
    for season in seasons:
        url = f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
        try:
            df = pd.read_csv(url, dtype=str)
            df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')
            
            # 抽取标准预测核心列
            core_cols = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'AvgH', 'AvgD', 'AvgA']
            df = df[[col for col in core_cols if col in df.columns]].copy()
            
            hist_dfs.append(df)
            print(f"Loaded {len(df)} matches from {url}")
        except Exception as e:

# --- 1.5. 抓取并清洗世界杯历史数据（全多表支持版） ---
print("Loading World Cup historical data from all sheets...")
world_cup_url = "https://www.football-data.co.uk/World_Cup.xlsx"

try:
    # 1. 一次性加载 Excel 的所有工作表（返回一个字典 {sheet_name: dataframe}）
    xl = pd.ExcelFile(world_cup_url)
    sheet_names = xl.sheet_names  # 获取所有的标签页名称：['WorldCup2026Qualifiers', 'WorldCup2022', ...]
    
    for sheet in sheet_names:
        print(f"Processing World Cup sheet: {sheet}")
        df_wc = xl.parse(sheet, dtype=str)
        
        # 2. 抹平列名差异（非常关键：把 Home/Away 映射为模型认识的 HomeTeam/AwayTeam）
        rename_dict = {'Home': 'HomeTeam', 'Away': 'AwayTeam'}
        df_wc = df_wc.rename(columns=rename_dict)
        
        # 3. 统一日期格式
        if 'Date' in df_wc.columns:
            df_wc['Date'] = pd.to_datetime(df_wc['Date'], format='mixed', dayfirst=True, errors='coerce')
        
        # 4. 补齐虚拟的 Div 联赛标记
        if 'Div' not in df_wc.columns:
            df_wc['Div'] = 'WC'
            
        # 5. 动态提取你模型需要的核心列（对应联赛 core_cols）
        wc_core_cols = [col for col in core_cols if col in df_wc.columns]
        df_wc_cleaned = df_wc[wc_core_cols].copy()
        
        # 6. 追加到总历史数据列表中
        if not df_wc_cleaned.empty:
            hist_dfs.append(df_wc_cleaned)
            print(f"Successfully loaded {len(df_wc_cleaned)} matches from {sheet}.")

except Exception as e:
    print(f"Failed to load World Cup data: {e}")
            
            print(f"Failed {url}: {e}")

# --- 2. 单独抓取并清洗日本联赛历史数据 ---
try:
    # 确保 URL 是这个全历史的独立链接
    j_url = "https://www.football-data.co.uk/new/JPN.csv"
    df_j = pd.read_csv(j_url, dtype=str)    
    df_j['Date'] = pd.to_datetime(df_j['Date'], format='mixed', dayfirst=True, errors='coerce')
    
    # 过滤掉太久远的历史（可选，加速运行）
    df_j = df_j[df_j['Date'] > '2023-01-01'].copy()
    
    # 字段改名
    rename_dict = {
        'League': 'Div',
        'Home': 'HomeTeam',
        'Away': 'AwayTeam',
        'HG': 'FTHG',
        'AG': 'FTAG'
    }
    df_j = df_j.rename(columns=rename_dict)
    
    # 【核心加入】把历史数据里的 "J1 League" 强行统一改为 "JPN"，和未来赛程表对齐
    df_j['Div'] = 'JPN'
    
    core_cols = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'AvgH', 'AvgD', 'AvgA']
    df_j = df_j[[col for col in core_cols if col in df_j.columns]].copy()
    
    hist_dfs.append(df_j)
    print(f"Successfully loaded and normalized {len(df_j)} J-League matches.")
except Exception as e:
    print(f"Failed to load Japan data: {e}")


# --- 3. 最终历史数据合并 ---
historical = pd.concat(hist_dfs, ignore_index=True) if hist_dfs else pd.DataFrame()
print(f"Total historical matches: {len(historical)}")

# --- 4. 未来赛程抓取与容错过滤 ---
url = "https://www.football-data.co.uk/fixtures.csv"
df = pd.read_csv(url, dtype=str)
df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')

print("当前未来赛程表里包含的所有联赛代码有:", df['Div'].unique())

today = datetime.now().date()
day_after = today + timedelta(days=3)

# 提取满足联赛和日期要求的比赛
mask_leagues = df['Div'].isin(PREDICT_LEAGUES)
mask_dates = (df['Date'].dt.date >= today) & (df['Date'].dt.date <= day_after)

# 组合过滤条件（去掉对 AvgH 强行 > 1 的硬性限制，改在下方进行填充）
upcoming = df[mask_leagues & mask_dates].copy()

# 如果有 AvgH 列，把不合法的空值填为 '2.5'，确保后续转 float 不崩
if 'AvgH' in upcoming.columns:
    upcoming['AvgH'] = upcoming['AvgH'].fillna('2.5')
else:
    upcoming['AvgH'] = '2.5'

print(f"Found {len(upcoming)} upcoming matches after relaxation.")

# 确保过滤使用的是包含 J 联赛的 PREDICT_LEAGUES 列表
upcoming = df[
    (df['Div'].isin(PREDICT_LEAGUES)) &
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
