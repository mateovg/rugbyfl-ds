import pandas as pd
from elo_calculator import EloCalculator

df = pd.read_csv('rugbyfl_data.csv')

elo = EloCalculator(df, k_factor=30, home_advantage=50)
seasons = df['season'].unique()

for season in seasons:
    elo.decay_season_ratings()
    elo.find_elo_ratings_season(season)

for k, v in sorted(elo.elo_dict.items(), key=lambda item: item[1], reverse=True):
    print(f"{k}: {v}")

elo.export_df("rugbyfl_elo.csv")
