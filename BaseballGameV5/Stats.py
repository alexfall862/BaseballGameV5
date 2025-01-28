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

def OutcomeStatAdder(batter, pitcher, stat):
    stattoadd = None
    if stat == "single":
        #print("single properly counted")
        stattoadd = "singles"
    if stat == "double":
        #print("double properly counted")
        stattoadd = "doubles"
    if stat == "triple":
        stattoadd = "triples"
    if stat == "homerun":
        stattoadd = "homeruns"
    if stattoadd != None:
        batter.battingstats.Adder(stattoadd, 1)
        pitcher.pitchingstats.Adder(stattoadd, 1)

def RunScorer(runner):
    runner.battingstats.Adder("runs", 1)
    if runner.earned_bool == True:
        runner.on_base_pitcher.pitchingstats.Adder("earned_runs", 1)
    else:
        runner.on_base_pitcher.pitchingstats.Adder("unearned_runs", 1)

class PitchingStats():
    def __init__(self, pid, position, name, teamname):
        self.pid = pid
        self.teamname = teamname
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
    def __init__(self, pid, position, name, teamname):
        self.pid = pid
        self.teamname = teamname
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
    def __init__(self, pid, position, name, teamname):
        self.pid = pid
        self.teamname = teamname
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
            self.avg = 0
            self.obp = 0
            self.slg = 0
            self.ops = 0
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
            #print(f"
            #
            #
            #
            #defense: {player.fieldingstats.pid}")
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

def StatJSONConverter(game):
    game.hometeam
    game.awayteam
    game.actions
    game.meta
    
    homebat, homepitch, homefield = TeamStatPull(game.hometeam)
    awaybat, awaypitch, awayfield = TeamStatPull(game.awayteam)
    #actions = ActionSort(game.actions)
    actions = game.actions

    homebatJSON = json.dumps([object.__dict__ for object in homebat])
    homepitchJSON = json.dumps([object.__dict__ for object in homepitch])
    homefieldJSON = json.dumps([object.__dict__ for object in homefield])
    awaybatJSON = json.dumps([object.__dict__ for object in awaybat])
    awaypitchJSON = json.dumps([object.__dict__ for object in awaypitch])
    awayfieldJSON = json.dumps([object.__dict__ for object in awayfield])
    actionsJSON = json.dumps([object for object in actions])
    gamemetaJSON = json.dumps( game.meta.to_dict())

    fullexport = {"result": json.loads(gamemetaJSON), "stats": {"batting": json.loads(homebatJSON) + json.loads(awaybatJSON), "pitching": json.loads(homepitchJSON) + json.loads(awaypitchJSON), "fielding": json.loads(homefieldJSON) + json.loads(awayfieldJSON), "playbyplay": json.loads(actionsJSON)}}


    #fullexport = [homebatJSON, homepitchJSON, homefieldJSON, awaybatJSON, awaypitchJSON, awayfieldJSON, actionsJSON]

    return fullexport

def ActionSort(actions):
    listofactions = []
    for action in actions:
        #print(action)
        listofactions.append(action)    
    export_dataframe = pd.DataFrame(listofactions)
    export_dataframe.replace({"None": ""}, inplace=True)
    return export_dataframe

def TeamStatPull(team):
    batting, test = StatPullBatting(team, "test")  
    pitching, test = StatPullPitching(team, "test")  
    fielding, test = StatPullFielding(team, "test")
    #batting = pd.DataFrame(batting)
    #pitching = pd.DataFrame(pitching)
    #fielding = pd.DataFrame(fielding)
    return batting, pitching, fielding


def SaveJSON(data, filestring):
    with open(str(filestring + ".json"), 'w') as jsonfile:
        json.dump(data, jsonfile)

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

def GameJSONCombiner(resultdict):
    battingstats = BatJSONCombiner(resultdict)
    pitchingstats = PitchJSONCombiner(resultdict)
    fieldingstats = FieldJSONCombiner(resultdict)
    resultsstats = ResultsJSONCombiner(resultdict)




def BatJSONCombiner(resultdict):
    batters = []
    for game in resultdict.values():
        for player in game['stats']['batting']:
            batstat = SCObject(**player)
            batters.append(batstat)
    batters = BatDeDuper(batters)
    for batter in batters:
        JSONCombineBat(batter)
        print(batter.__dict__)
    return batters

def PitchJSONCombiner(resultdict):
    pitchers = []
    for game in resultdict.values():
        for player in game['stats']['pitching']:
            pitchstat = SCObject(**player)
            pitchers.append(pitchstat)
    pitchers = PitchDeDuper(pitchers)
    for pitcher in pitchers:
        JSONCombinePitch(pitcher)
        print(pitcher.__dict__)
    return pitchers

def FieldJSONCombiner(resultdict):
    fielders = []
    for game in resultdict.values():
        for player in game['stats']['fielding']:
            fieldstat = SCObject(**player)
            fielders.append(fieldstat)
    fielders = FieldDeDuper(fielders)
    for fielder in fielders:
        JSONCombineField(fielder)
        print(fielder.__dict__)
    return fielders

def ResultsJSONCombiner(resultdict):
    results = []
    for game in resultdict.values():
        for result in game['result']:
            result_obj = SCObject(**result)
            results.append(result_obj)
    results = ResultsDeDuper(results)
    for result in results:
        JSONCombineResults(result)
        print(result.__dict__)
    return results




class SCObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def PitchDeDuper(pitchers):
    return pitchers

def FieldDeDuper(fielders):
    return fielders

def ResultsDeDuper(results):
    return results

def BatDeDuper(players):
    result = {}
    for player in players:
        if player.pid in result:
            result[player.pid].games_started += player.games_started
            result[player.pid].game_appearances += player.game_appearances
            result[player.pid].at_bats += player.at_bats
            result[player.pid].runs += player.runs
            result[player.pid].singles += player.singles
            result[player.pid].doubles += player.doubles
            result[player.pid].triples += player.triples
            result[player.pid].homeruns += player.homeruns
            result[player.pid].stolen_bases += player.stolen_bases
            result[player.pid].caught_stealing += player.caught_stealing
            result[player.pid].walks += player.walks
            result[player.pid].strikeouts += player.strikeouts
            result[player.pid].hbp += player.hbp
            result[player.pid].ibb += player.ibb
            result[player.pid].bases += player.bases
            result[player.pid].triples += player.triples
            result[player.pid].triples += player.triples
            result[player.pid].triples += player.triples
            result[player.pid].triples += player.triples

        else:
            result[player.pid] = player
    return list(result.values())


def JSONCombineBat(batstats):
    batstats.hits = batstats.singles + batstats.doubles + batstats.triples + batstats.homeruns
    batstats.totalbases = ((1*batstats.singles) + (2*batstats.doubles) + (3*batstats.triples) + (4*batstats.homeruns))
    if batstats.at_bats == 0:
        batstats.avg = 0
        batstats.obp = 0
        batstats.slg = 0
        batstats.ops = 0
    else:
        batstats.avg = round( (batstats.hits/batstats.at_bats), 3 )
        batstats.obp = round( (batstats.hits + batstats.walks + batstats.hbp)/(batstats.at_bats + batstats.walks + batstats.hbp), 3 )
        batstats.slg = round( batstats.totalbases/batstats.at_bats, 3)
        batstats.ops = round( (batstats.obp + batstats.slg), 3 )
