import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
import json
import os

LEAGUES = ["E0", "E1", "E2", "SP1", "SP2", "I1", "F1", "F2", "D1", "D2", "P1"]
# 把预测目标改为：现有欧洲联赛 + 挪威超(N1) + 刚加入的世界杯(WC)
PREDICT_LEAGUES = LEAGUES + ["N1", "WC"]
MIN_EDGE = 0.05

print("Loading extensive historical data for rich H2H...")
hist_dfs = []
seasons = ["2526", "2425", "2324"]

# --- 1. 遍历下载并清洗欧洲主流联赛历史数据 ---
print("Loading European historical data...")
for league in LEAGUES:
    for season in seasons:
        url = f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
        try:
            df = pd.read_csv(url, dtype=str)
            df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')
            core_cols = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'AvgH', 'AvgD', 'AvgA']
            df = df[[col for col in core_cols if col in df.columns]].copy()
            hist_dfs.append(df)
            print(f"loaded {len(df)} matches from {url}")
        except Exception as e:
            print(f"Failed {url}: {e}")

# --- 1.5 批量抓取扩展联赛历史数据（挪威、日本、美国、瑞典、芬兰、巴西等） ---
extra_leagues_config = [
    {"url": "https://www.football-data.co.uk/new/NOR.csv", "div": "N1", "name": "Norway Eliteserien"},
    {"url": "https://www.football-data.co.uk/new/JPN.csv", "div": "J1", "name": "Japan J-League"},
    {"url": "https://www.football-data.co.uk/new/KOR.csv", "div": "K1", "name": "Korea K-League"},
    {"url": "https://www.football-data.co.uk/new/USA.csv", "div": "USA", "name": "USA MLS"},
    {"url": "https://www.football-data.co.uk/new/SWE.csv", "div": "SWE", "name": "Sweden Allsvenskan"},
    {"url": "https://www.football-data.co.uk/new/FIN.csv", "div": "FIN", "name": "Finland Veikkausliiga"},
    {"url": "https://www.football-data.co.uk/new/BRA.csv", "div": "BRA", "name": "Brazil Serie A"}
]

# extra csv 的列名映射规则
rename_extra = {
    'Home': 'HomeTeam',
    'Away': 'AwayTeam',
    'HG': 'FTHG',
    'AG': 'FTAG'
}

for item in extra_leagues_config:
    print(f"Loading {item['name']} historical data...")
    try:
        df_extra = pd.read_csv(item['url'], dtype=str)
        
        # 1. 统一列名映射（将扩展格式转换为欧洲主流联赛格式）
        df_extra = df_extra.rename(columns=rename_extra)
        
        # 2. 覆盖/赋值标准的 Div 代号
        df_extra['Div'] = item['div']
        
        # 3. 解析日期
        if 'Date' in df_extra.columns:
            df_extra['Date'] = pd.to_datetime(df_extra['Date'], format='mixed', dayfirst=True, errors='coerce')
        
        # 4. 抽取所需核心列
        core_cols = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'AvgH', 'AvgD', 'AvgA']
        df_extra = df_extra[[col for col in core_cols if col in df_extra.columns]].copy()
        
        # 5. 过滤掉尚未完成比赛（比分为空）的行
        df_extra = df_extra.dropna(subset=['FTHG', 'FTAG'])
        
        hist_dfs.append(df_extra)
        print(f"Successfully loaded {len(df_extra)} matches for {item['name']}")
    except Exception as e:
        print(f"Failed to load {item['name']} data: {e}")
        
# --- 2. 抓取并清洗世界杯历史数据（本地完美离线版） ---
print("Loading World Cup historical data from local storage...")
# 直接读取你刚刚上传到 backend 目录下的本地 Excel 文件

# 1. 正常的动态绝对路径
base_dir = os.path.dirname(os.path.abspath(__file__))
world_cup_path = os.path.join(base_dir, "WorldCup.xlsx")

# 2. 针对 GitHub Actions 双层嵌套环境的容错兜底
if not os.path.exists(world_cup_path):
    # 如果当前在双层目录下，尝试往上返一级找 backend 目录
    parent_dir = os.path.dirname(base_dir)
    backup_path = os.path.join(parent_dir, "backend", "WorldCup.xlsx")
    if os.path.exists(backup_path):
        world_cup_path = backup_path
    else:
        # 再尝试直接在当前工作根目录下找 backend/WorldCup.xlsx
        backup_path_2 = os.path.join(os.getcwd(), "backend", "WorldCup.xlsx")
        if os.path.exists(backup_path_2):
            world_cup_path = backup_path_2

try:
    print("Loading World Cup historical data from local storage...")
    # 1. 初始化一个空列表，防止后面报错
    sheet_names = [] 
    
    if os.path.exists(world_cup_path):
        xl = pd.ExcelFile(world_cup_path)
        sheet_names = xl.sheet_names  # 自动读取：['WorldCup2026Qualifiers', 'WorldCup2022', ...]
        
    for sheet in sheet_names:
        if "Qualifiers" in sheet:
            print(f"Skipping {sheet} to prevent model convergence failure.")
        continue
            
        print(f"Processing local World Cup sheet: {sheet}")
        df_wc = xl.parse(sheet, dtype=str)
            
        # 1. 强制重命名：确保名字和欧洲联赛完全一致
        rename_dict = {
            'Home': 'HomeTeam', 
            'Away': 'AwayTeam', 
            'HG': 'FTHG',     
            'AG': 'FTAG'      
        }
        df_wc = df_wc.rename(columns=rename_dict)
            
        if 'Date' in df_wc.columns:
            df_wc['Date'] = pd.to_datetime(df_wc['Date'], format='mixed', dayfirst=True, errors='coerce')
            
        if 'Div' not in df_wc.columns:
            df_wc['Div'] = 'WC'
                
        # 2. 提取核心列
        core_cols = ['Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'AvgH', 'AvgD', 'AvgA']
        wc_core_cols = [col for col in core_cols if col in df_wc.columns]
        df_wc_cleaned = df_wc[wc_core_cols].copy()
        
        # 3. 🔥【核心修复】强制将进球数转换为数字类型，非数字的会变成 NaN
        df_wc_cleaned['FTHG'] = pd.to_numeric(df_wc_cleaned['FTHG'], errors='coerce')
        df_wc_cleaned['FTAG'] = pd.to_numeric(df_wc_cleaned['FTAG'], errors='coerce')
        
        # 4. 彻底剔除掉没有进球数字的行（包括还没踢的未来赛程）
        df_wc_cleaned = df_wc_cleaned.dropna(subset=['FTHG', 'FTAG'])
        
        # 5. 确保转换成与欧洲联赛一致的整数型
        df_wc_cleaned['FTHG'] = df_wc_cleaned['FTHG'].astype(int)
        df_wc_cleaned['FTAG'] = df_wc_cleaned['FTAG'].astype(int)
            
        if not df_wc_cleaned.empty:
            hist_dfs.append(df_wc_cleaned)
            print(f"Successfully loaded {len(df_wc_cleaned)} matches from local sheet: {sheet}.")
    else:
        print(f"Warning: Local World Cup file not found at {world_cup_path}, skipping.")
        
except Exception as e:
    print(f"Failed to load local World Cup data: {e}")


# --- 3. 合并所有载入的数据 ---
if hist_dfs:
    final_df = pd.concat(hist_dfs, ignore_index=True)
    print(f"Total dataset size: {len(final_df)} matches.")
else:
    print("No data loaded. Skipping pipeline.")

# --- 4. 未来赛程抓取与容错过滤 ---
print("Fetching upcoming fixtures from main and extra sources...")

fixture_urls = [
    "https://www.football-data.co.uk/fixtures.csv",
    "https://www.football-data.co.uk/new_fixtures.csv"
]

fixture_dfs = []
for f_url in fixture_urls:
    try:
        # 去掉可能的误打空格
        clean_url = f_url.strip()
        f_df = pd.read_csv(clean_url, dtype=str)
        
        # 统一扩展联赛列名映射（Home->HomeTeam, Away->AwayTeam）
        rename_fixture = {
            'Home': 'HomeTeam', 
            'Away': 'AwayTeam', 
            'HG': 'FTHG', 
            'AG': 'FTAG'
        }
        f_df = f_df.rename(columns=rename_fixture)
        
        fixture_dfs.append(f_df)
        print(f"Successfully fetched fixtures from {clean_url}")
    except Exception as e:
        print(f"Warning: Could not fetch fixtures from {f_url}: {e}")

if fixture_dfs:
    df = pd.concat(fixture_dfs, ignore_index=True)
else:
    df = pd.DataFrame()

if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')

    if 'Div' in df.columns:
        print("当前未来赛程表里包含的所有联赛代码:", df['Div'].unique())

    today = datetime.now().date()
    # 延长预测窗口至 14 天
    day_after = today + timedelta(days=14)

    # 包含别名匹配，防止联赛代号不一致
    EXTRA_DIVS = ["N1", "NOR", "J1", "JPN", "K1", "KOR", "USA", "SWE", "S1", "FIN", "F1", "BRA", "B1"]
    ALL_LEAGUES = LEAGUES + EXTRA_DIVS + ["WC"]

    mask_leagues = df['Div'].isin(ALL_LEAGUES)
    mask_dates = (df['Date'].dt.date >= today) & (df['Date'].dt.date <= day_after)

    upcoming = df[mask_leagues & mask_dates].copy()
else:
    upcoming = pd.DataFrame()
    
print("当前未来赛程表里包含的所有联赛代码有:", df['Div'].unique())

today = datetime.now().date()
# 将 timedelta(days=3) 改为 7 或 14，可以覆盖到下个周末的全部比赛
day_after = today + timedelta(days=7)

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
