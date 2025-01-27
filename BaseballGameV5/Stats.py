import pandas as pd
import csv
import json 

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
    #print(uniqueinnings)

class InningStats():
    def __init__(self, inning, team, score):
        self.inning = inning
        self.team = team
        self.score = score
    def __repr__(self):
        return f"{self.inning, self.team, self.score}"

def OutcomeStatAdder(pitcher, batter, stat):
    if stat == "single":
        stattoadd = "singles"
    if stat == "double":
        stattoadd = "doubles"
    if stat == "triple":
        stattoadd = "triples"
    if stat == "homeruns":
        stattoadd = "homeruns"



    #pitcher.pitchingstats.Adder(stattoadd, 1)
    pass


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
        self.balls = 0
        self.strikes = 0
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
        self.hits_allowed = (self.singles + self.doubles + self.triples + self.homeruns)
        self.whip = round( ((self.walks + self.hits_allowed)/self.innings_pitched), 3)
        self.fip = round( (((13*self.homeruns) + (3*(self.walks+self.hbp)) - (2*self.strikeouts))/self.innings_pitched), 3 )

    def Adder(self, stat_name, amount):
        current_value = getattr(self, stat_name)
        new_value = current_value+amount
        setattr(self, stat_name, new_value)

class FieldingStats():
    def __init__(self, pid, position, name):
        self.pid = pid
        self.position = position
        self.name = name
        self.throwing_errors = 0
        self.catching_errors = 0
        self.assists = 0
        self.putouts = 0
        self.innings_played = 0
      
    def Combiner(self):
        self.errors = self.throwing_errors + self.catching_errors
        self.defensive_chances = self.putouts + self.assists + self.errors
        if self.defensive_chances == 0:
            self.fielding_percentage = None
        else:
            self.fielding_percentage = round(((self.putouts+self.assists) / self.defensive_chances), 3)
            
    def Adder(self, stat_name, amount):
        current_value = getattr(self, stat_name)
        new_value = current_value+amount
        setattr(self, stat_name, new_value)

class BattingStats():
    def __init__(self, pid, position, name):
        self.pid = pid
        self.position = position
        self.name = name
        self.games_started = 0
        self.game_appearances = 0
        self.at_bats = 0
        self.plate_appearances = 0
        self.runs = 0
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
        self.bases = 0
        
    def Combiner(self):
        self.hits = self.singles + self.doubles + self.triples + self.homeruns
        self.totalbases = ((1*self.singles) + (2*self.doubles) + (3*self.triples) + (4*self.homeruns))
        if self.at_bats == 0:
            pass
        else:
            self.avg = round( (self.hits/self.at_bats), 3 )
            self.obp = round( (self.hits + self.walks + self.hbp)/(self.at_bats + self.walks + self.hbp), 3 )
            self.slg = round( self.totalbases/self.at_bats, 3)
            self.ops = round( (self.obp + self.slg), 3 )

    def Adder(self, stat_name, amount):
        current_value = getattr(self, stat_name)
        new_value = current_value+amount
        setattr(self, stat_name, new_value)

def SetPitcherStatus(player, pitcher, earned_bool):
    player.earned_bool = earned_bool
    player.on_base_pitcher = pitcher.id
    
def ResetPitcherStatus(player):
    player.earned_bool = True
    player.on_base_pitcher = None

def StatPullFielding(team, gname):
    export = [] 
    filename = str(f"{gname}_defense_{team.name}")    
    for player in team.roster.playerlist:
        if player.fieldingstats.innings_played > 0:
            player.fieldingstats.Combiner()
            export.append(player.fieldingstats)
            #print(f"defense: {player.fieldingstats.pid}")
    return export, filename

def StatPullPitching(team, gname):
    export = [] 
    filename = str(f"{gname}_pitching_{team.name}")    
    for player in team.roster.playerlist:
        if player.pitchingstats.pitches_thrown > 0:
            player.pitchingstats.Combiner()
            export.append(player.pitchingstats)
            #print(f"defense: {player.pitchingstats.pid}")
    return export, filename

def StatPullBatting(team, gname):
    export = [] 
    filename = str(f"{gname}_batting_{team.name}")    
    for player in team.roster.playerlist:
        if player.battingstats.plate_appearances > 0:
            player.battingstats.Combiner()
            export.append(player.battingstats)
            #print(f"defense: {player.battingstats.pid}")
    return export, filename

def FieldStatPullSave(team, gname):
    export, filename = StatPullFielding(team, gname)
    StatSaverCombo(export, filename)
    
def PitchStatPullSave(team, gname):
    export, filename = StatPullPitching(team, gname)
    StatSaverCombo(export, filename)
    
def BattingStatPullSave(team, gname):
    export, filename = StatPullBatting(team, gname)
    StatSaverCombo(export, filename)


def StatSaverCSV(objects, filename):
    with open(str(filename+".csv"), 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=objects[0].__dict__.keys())
        writer.writeheader()
        for object in objects:
            writer.writerow(object.__dict__)

def StatSaverJSON(objects, filename):
    with open(str(filename + ".json"), 'w') as jsonfile:
        json.dump([object.__dict__ for object in objects], jsonfile)
        
def StatSaverCombo(objects, filename):
    StatSaverCSV(objects, filename)
    StatSaverJSON(objects, filename)