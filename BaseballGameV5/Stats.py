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
    def __init__(self, pid, position, name):
        self.pid = pid
        self.position = position
        self.name = name
        self.win = 0
        self.loss = 0
        self.earned_runs = 0
        self.unearned_runs = 0
        self.innings_pitched = 0 #incremented in thirds?
        self.pitches_thrown = 0
        self.balls_thrown = 0
        self.strikes_thrown = 0
        self.walks = 0
        self.strikeouts = 0
        self.homeruns = 0
        self.triples = 0
        self.doubles = 0
        self.singles = 0
        self.hbp = 0
        self.ibb = 0
        self.wildpitches = 0
        self.balks = 0
        self.games_started = 0
        self.appearances = 0
        
    def Combiner(self):
        self.era = round( (9*self.earned_runs / self.innings_pitched), 3)
        self.hits_allowed = (self.single + self.double + self.triple + self.homerun)
        self.whip = round( ((self.walks + self.hits_allowed)/self.innings_pitched), 3)
        self.fip = round( (((13*self.homeruns) + (3*(self.walks+self.hbp)) - (2*self.strikeouts))/self.innings_pitched), 3 )

class FieldingStats():
    def __init__(self, pid, position, name):
        self.pid = pid
        self.position = position
        self.name = name
        self.errors = 0
        self.outs = 0
        self.assists = 0
        self.putouts = 0
        self.innings_played = 0
      
    def Combiner(self):
        self.defensive_chances = self.putouts + self.assists + self.errors
        self.fielding_percentage = round(((self.putouts+self.assists) / self.defensive_chances), 3)

class BattingStats():
    def __init__(self, pid, position, name):
        self.pid = pid
        self.position = position
        self.name = name
        self.games_started = 0
        self.appearances = 0
        self.at_bats = 0
        self.plate_appearances = 0
        self.runs_scored = 0
        self.singles = 0
        self.doubles = 0
        self.triples = 0
        self.homeruns = 0
        self.stolen_bases = 0
        self.caught_stealing = 0
        self.walks = 0
        self.strikeouts = 0
        self.hbp = 0
        self.ibb = 0
        
    def Combiner(self):
        self.hits = self.singles + self.doubles + self.triples + self.homeruns
        self.avg = round( (self.hits/self.at_bats), 3 )
        self.obp = round( (self.hits + self.walks + self.hbp)/(self.at_bats + self.walks + self.hbp), 3 )
        self.totalbases = ((1*self.singles) + (2*self.doubles) + (3*self.triples) + (4*self.homeruns))
        self.slg = round( self.totalbases/self.at_bats, 3)
        self.ops = round( (self.obp + self.slg), 3 )

