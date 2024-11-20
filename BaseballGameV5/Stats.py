import pandas as pd

def create_score_table(objects):
    data = {}
    for obj in objects:
        team_name = obj.team
        inning = obj.inning
        score = obj.score

        if team_name not in data:
            data[team_name] = {}
        data[team_name][inning] =  int(score)

    df = pd.DataFrame(data)
    df = df.T
    df = df.sort_index(axis=1)

    for team in df.index:
        previous_score = 0
        for inning in df.columns:
            current_score = df.loc[team, inning]
            df.loc[team, inning] = current_score - previous_score
            previous_score = current_score
    df['Total'] = df.sum(axis=1)
    df.fillna(0, inplace=True)
    df = df.astype(int)
    return df

def Inning_Tabulator(listofinnings):
    uniqueinnings = set(x.inning for x in listofinnings)
    print(uniqueinnings)

class InningStats():
    def __init__(self, inning, team, score):
        self.inning = inning
        self.team = team
        self.score = score
    def __repr__(self):
        return f"{self.inning, self.team, self.score}"

class PitchingStats():
    def __init__(self):
        pass

class FieldingStats():
    def __init__(self):
        pass

class BattingStats():
    def __init__(self):
        pass




