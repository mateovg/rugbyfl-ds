# functions to calculate each part of the elo formula

class Elo:
    def __init__(self, df: DataFrame, k_factor=20, home_advantage=100):
        self.k_factor = k_factor
        self.home_advantage = home_advantage

    def find_K(self, margin_of_victory: int, elo_diff: int) -> int:
        # K is multiplier to apply to the elo change
        # the multiplier function is from 538, as is the k_0 value
        # positive MOV means home team won
        k_factor = self.k_factor
        if margin_of_victory > 0:
            multiplier = (margin_of_victory + 3) ** 0.8 / (7.5 + 0.006 * elo_diff)
        else:
            multiplier = (-margin_of_victory + 3) ** 0.8 / (7.5 + 0.006 * -elo_diff)
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

    def find_new_elo(self, elo_home, elo_away, margin_of_victory):
        elo_diff = elo_home - elo_away
        K_home, K_away = self.find_K(margin_of_victory, elo_diff)
        S_home, S_away = self.find_S(margin_of_victory)
        E_home, E_away = self.find_E(elo_home, elo_away)

        elo_home = elo_home + K_home * (S_home - E_home)
        elo_away = elo_away + K_away * (S_away - E_away)

        return elo_home, elo_away

    def find_decay_elo(self, elo):
        # 1505 to aim for a 1500 mean
        # due to new teams joining the league
        return elo * 0.75 + 1505 * 0.25

    def find_elo_ratings(self, season, elo_dict):
        # loop through each game and calculate the new elo rating for each team
        # each row should have the elo rating BEFORE the game

        for index, row in season.iterrows():
            home_team = row['team_name_home']
            away_team = row['team_name_away']

            elo_home = elo_dict[home_team]
            elo_away = elo_dict[away_team]

            season.loc[index, 'elo_home'] = elo_home
            season.loc[index, 'elo_away'] = elo_away

            MOV = row['plus_minus_home']

            elo_home_new, elo_away_new = self.find_new_elo(
                elo_home, elo_away, MOV)

            elo_dict[home_team] = elo_home_new
            elo_dict[away_team] = elo_away_new
