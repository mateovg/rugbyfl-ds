# functions to calculate each part of the elo formula
from dataclasses import dataclass
import datetime
from pandas import DataFrame


@dataclass
class Match:
    Game_ID: int
    Championship_ID: int
    Team_ID: int
    Team_Name: str
    Team_Score: int
    Opponent_ID: int
    Opponent_Name: str
    Opponent_Score: int
    Game_Date: datetime
    Season: int
    Is_Home: bool
    Team_ELO: int
    ELO_Change: int
    Opponent_ELO: int


class EloCalculator:
    def __init__(self, df: DataFrame, k_factor=20, home_advantage=100, starting_elo=1505):
        self.df = df.copy()  # dataframe with all the games
        self.elo_dict = {}  # dictionary with team names as keys and elo ratings as values
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.starting_elo = starting_elo
        self.init_elo_dict()

    def get_df(self):
        return self.df.copy()

    def print_elo_changes(self, team_name):
        team_df = (self.df[self.df['Team_Name'] ==
                           team_name])
        for index, row in team_df.iterrows():
            print(
                f"{row['Game_Date']} - {row['Team_Name']} vs {row['Opponent_Name']}: {row['ELO_Change']}, ELO: {row['Team_ELO']}")

    def find_elo_ratings_season(self, season: int):
        season_df = self.df[self.df['Season'] == season]
        games = season_df['Game_ID'].unique()

        for game_id in games:
            home_row = season_df[(season_df['Game_ID'] == game_id) & (
                season_df['Is_Home'] == True)]
            away_row = season_df[(season_df['Game_ID'] == game_id) & (
                season_df['Is_Home'] == False)]

            home_team = home_row.iloc[0]['Team_Name']
            away_team = away_row.iloc[0]['Team_Name']

            home_elo = self.elo_dict.get(home_team, 1505)
            away_elo = self.elo_dict.get(away_team, 1505)

            if home_elo > 1800:
                print(f"{game_id} - {home_team} has an elo of {home_elo}")
            if away_elo > 1800:
                print(f"{game_id} - {away_team} has an elo of {away_elo}")

            if home_team in ["Out of State", "Miami Sharks"]:
                home_elo = away_elo
            if away_team in ["Out of State", "Miami Sharks"]:
                away_elo = home_elo + self.home_advantage

            # Update DataFrame with current Elo ratings
            self.df.loc[home_row.index, 'Team_ELO'] = home_elo
            self.df.loc[away_row.index, 'Team_ELO'] = away_elo
            self.df.loc[away_row.index, 'Opponent_ELO'] = home_elo
            self.df.loc[home_row.index, 'Opponent_ELO'] = away_elo

            home_score = home_row.iloc[0]['Team_Score']
            away_score = away_row.iloc[0]['Team_Score']

            margin_of_victory = home_score - away_score

            home_elo_change, away_elo_change = self.find_elo_change(
                home_elo, away_elo, margin_of_victory)

            # Update elo_dict with new elo ratings
            self.elo_dict[home_team] = home_elo + home_elo_change
            self.elo_dict[away_team] = away_elo + away_elo_change

            # Update DataFrame with Elo changes
            self.df.loc[home_row.index, 'ELO_Change'] = home_elo_change
            self.df.loc[away_row.index, 'ELO_Change'] = away_elo_change

    def init_elo_dict(self):
        teams = self.df['Team_Name'].unique()
        for team in teams:
            if team not in self.elo_dict:
                self.elo_dict[team] = self.starting_elo

    def decay_season_ratings(self):
        """
        Decay the elo ratings by 25% to the mean, set at 1505 to account for
        changes in the off season.
        """
        for team in self.elo_dict:
            self.elo_dict[team] = self.find_decay_elo(self.elo_dict[team])

    def find_elo_change(self, home_elo: int, away_elo: int, margin_of_victory: int) -> tuple[int, int]:
        elo_diff = home_elo - away_elo

        K_home, K_away = self.find_K(margin_of_victory, elo_diff)
        S_home, S_away = self.find_S(margin_of_victory)
        E_home, E_away = self.find_E(home_elo, away_elo)

        home_elo = K_home * (S_home - E_home)
        away_elo = K_away * (S_away - E_away)

        return int(home_elo), int(away_elo)

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
