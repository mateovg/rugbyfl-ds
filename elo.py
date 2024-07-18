# functions to calculate each part of the elo formula

from pandas import DataFrame


class Elo:
    def __init__(self, df: DataFrame, k_factor=20, home_advantage=100, starting_elo=1505):
        self.df = df  # dataframe with all the games
        self.elo_dict = {}  # dictionary with team names as keys and elo ratings as values
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.starting_elo = starting_elo
        self.init_elo_dict()

    def find_elo_ratings_season(self, season: int):
        season_df = self.df[self.df['Season'] == season].copy()
        games = season_df['Game_ID'].unique()

        for game_id in games:
            home_row = season_df[(season_df['Game_ID'] == game_id) & (
                season_df['Is_Home'] == 1)]
            away_row = season_df[(season_df['Game_ID'] == game_id) & (
                season_df['Is_Home'] == 0)]

            home_team = home_row['Team_Name']
            away_team = away_row['Opponent_Name']

            margin_of_victory = home_row['Team_Score'] - away_row['Team_Score']

            home_elo_change, away_elo_change = self.find_elo_change(
                home_team, away_team, margin_of_victory)

            # Update rows with new elo ratings

            self.elo_dict[away_team] += away_elo_change
            self.elo_dict[home_team] += home_elo_change

        return season

    def init_elo_dict(self):
        teams = self.df['Team_Name'].unique()
        for team in teams:
            self.elo_dict[team] = self.starting_elo

    def find_elo_ratings_season_decay(self, season: DataFrame, elo_dict: dict):
        for team in elo_dict:
            elo_dict[team] = self.find_decay_elo(elo_dict[team])
        return elo_dict

    def find_elo_change(self, home_team: str, away_team: str, margin_of_victory: int):
        elo_home = self.elo_dict[home_team]
        elo_away = self.elo_dict[away_team]

        elo_diff = elo_home - elo_away

        K_home, K_away = self.find_K(margin_of_victory, elo_diff)
        S_home, S_away = self.find_S(margin_of_victory)
        E_home, E_away = self.find_E(elo_home, elo_away)

        elo_home = K_home * (S_home - E_home)
        elo_away = K_away * (S_away - E_away)

        return int(elo_home), int(elo_away)

    def find_K(self, margin_of_victory: int, elo_diff: int) -> int:
        # K is multiplier to apply to the elo change
        # the multiplier function is from 538, as is the k_0 value
        # positive MOV means home team won
        k_factor = self.k_factor
        if margin_of_victory > 0:  # home team won
            multiplier = (margin_of_victory + 3) ** 0.8 / \
                (7.5 + 0.006 * elo_diff)
        else:  # home team lost
            multiplier = (-margin_of_victory + 3) ** 0.8 / \
                (7.5 + 0.006 * -elo_diff)
        # returns two values, one for each team
        return k_factor * multiplier, k_factor * multiplier

    def find_S(self, margin_of_victory: int):
        if margin_of_victory > 0:  # home team won
            return 1, 0
        elif margin_of_victory < 0:  # home team lost
            return 0, 1
        else:
            return 0.5, 0.5  # tie

    def find_E(self, elo_home: int, elo_away: int) -> tuple[float, float]:
        home_adv = self.home_advantage
        elo_home += home_adv

        E_home = 1 / (1 + 10 ** ((elo_away - elo_home) / 400.0))
        E_away = 1 / (1 + 10 ** ((elo_home - elo_away) / 400.0))

        return E_home, E_away

    def find_decay_elo(self, elo: int) -> int:
        """
        Decay the elo rating by 25% to the mean, set at 1505 to account for
        new teams joining. 
        """
        return int(elo * 0.75 + 1505 * 0.25)
