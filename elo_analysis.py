import pandas as pd
from elo import EloCalculator

df = pd.read_csv('rugbyfl_data.csv')

elo = EloCalculator(df)
seasons = df['Season'].unique()
for season in seasons:
    elo.decay_season_ratings()
    elo.find_elo_ratings_season(season)

# for k, v in sorted(elo.elo_dict.items(), key=lambda item: item[1], reverse=True):
#     print(f"{k}: {v}")

df = elo.get_df()
df.to_csv('rugbyfl_elo.csv', index=False)
