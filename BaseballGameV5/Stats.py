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

    import pandas as pd
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
    if stat == "homerun" or stat == "inside_the_park_hr":
        stattoadd = "homeruns"
    if stattoadd != None:
        batter.battingstats.Adder(stattoadd, 1)
        pitcher.pitchingstats.Adder(stattoadd, 1)

def RunScorer(runner):
    runner.battingstats.Adder("runs", 1)
    if runner.on_base_pitcher is not None:
        if runner.earned_bool == True:
            runner.on_base_pitcher.pitchingstats.Adder("earned_runs", 1)
        else:
            runner.on_base_pitcher.pitchingstats.Adder("unearned_runs", 1)

def outs_to_innings(outs):
    """Convert outs count to baseball innings notation (e.g., 27 outs = 9.0, 28 outs = 9.1)."""
    full_innings = outs // 3
    partial = outs % 3
    return full_innings + (partial / 10.0)


def innings_to_outs(innings):
    """Convert baseball innings notation to outs count (e.g., 9.1 = 28 outs)."""
    full_innings = int(innings)
    partial = round((innings - full_innings) * 10)
    return (full_innings * 3) + partial


class PitchingStats():
    def __init__(self, pid, position, name, teamname):
        self.pid = pid
        self.teamname = teamname
        self.position = position
        self.name = name
        self.win = 0
        self.loss = 0
        self.save = 0
        self.earned_runs = 0
        self.unearned_runs = 0
        self.outs_pitched = 0  # Store as integer outs
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
        self.hold = 0
        self.blown_save = 0
        self.quality_start = 0
        # Expanded counting stats
        self.batters_faced = 0
        self.sacrifice_flies_allowed = 0
        self.gidp_induced = 0
        self.ground_balls_allowed = 0
        self.fly_balls_allowed = 0
        self.popups_allowed = 0
        self.inherited_runners = 0
        self.inherited_runners_scored = 0
        # Raw contact type counters
        self.contact_barrel = 0
        self.contact_solid = 0
        self.contact_flare = 0
        self.contact_burner = 0
        self.contact_under = 0
        self.contact_topped = 0
        self.contact_weak = 0

    @property
    def innings_pitched(self):
        """Convert outs to baseball innings notation for display."""
        return outs_to_innings(self.outs_pitched)

    def Combiner(self):
        # Use actual innings (outs/3) for rate calculations, not display notation
        actual_innings = self.outs_pitched / 3 if self.outs_pitched > 0 else 1
        self.era = round((9 * self.earned_runs / actual_innings), 3)
        self.hits_allowed = (self.singles + self.doubles + self.triples + self.homeruns)
        self.whip = round(((self.walks + self.hits_allowed) / actual_innings), 3)
        self.fip = round((((13 * self.homeruns) + (3 * (self.walks + self.hbp)) - (2 * self.strikeouts)) / actual_innings), 3)

    def Adder(self, stat_name, amount):
        current_value = getattr(self, stat_name)
        new_value = current_value + amount
        setattr(self, stat_name, new_value)

    def to_dict(self):
        """Return dict with innings_pitched as display value instead of outs."""
        d = self.__dict__.copy()
        d['innings_pitched'] = self.innings_pitched  # Add computed property
        del d['outs_pitched']  # Remove internal outs tracking
        return d

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
        self.outs_played = 0  # Store as integer outs
        self.double_plays_turned = 0

    @property
    def innings_played(self):
        """Convert outs to baseball innings notation for display."""
        return outs_to_innings(self.outs_played)

    def Combiner(self):
        self.errors = self.throwing_errors + self.catching_errors
        self.defensive_chances = self.putouts + self.assists + self.errors
        if self.defensive_chances == 0:
            self.fielding_percentage = None
        else:
            self.fielding_percentage = round(((self.putouts + self.assists) / self.defensive_chances), 3)

    def Adder(self, stat_name, amount):
        current_value = getattr(self, stat_name)
        new_value = current_value + amount
        setattr(self, stat_name, new_value)

    def to_dict(self):
        """Return dict with innings_played as display value instead of outs."""
        d = self.__dict__.copy()
        d['innings_played'] = self.innings_played  # Add computed property
        del d['outs_played']  # Remove internal outs tracking
        return d

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
        self.rbi = 0
        self.bases = 0
        # Batted ball type counters
        self.sacrifice_flies = 0
        self.gidp = 0
        self.ground_balls = 0
        self.fly_balls = 0
        self.popups = 0
        # Raw contact type counters
        self.contact_barrel = 0
        self.contact_solid = 0
        self.contact_flare = 0
        self.contact_burner = 0
        self.contact_under = 0
        self.contact_topped = 0
        self.contact_weak = 0
        
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
    player.on_base_pitcher = pitcher
    
def ResetPitcherStatus(player):
    player.earned_bool = True
    player.on_base_pitcher = None

def StatPullFielding(team, gname):
    export = []
    filename = str(f"{gname}_defense_{team.name}")
    for player in team.roster.playerlist:
        if player.fieldingstats.outs_played > 0:
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
    homebat, homepitch, homefield = TeamStatPull(game.hometeam)
    awaybat, awaypitch, awayfield = TeamStatPull(game.awayteam)

    fullexport = {
        "result": game.meta.to_dict(),
        "stats": {
            "batting": [obj.__dict__ for obj in homebat] + [obj.__dict__ for obj in awaybat],
            "pitching": [obj.to_dict() for obj in homepitch] + [obj.to_dict() for obj in awaypitch],
            "fielding": [obj.to_dict() for obj in homefield] + [obj.to_dict() for obj in awayfield],
            "playbyplay": list(game.actions)
        }
    }

    return fullexport

def ActionSort(actions):
    import pandas as pd
    listofactions = []
    for action in actions:
        listofactions.append(action)
    export_dataframe = pd.DataFrame(listofactions)
    export_dataframe.replace({"None": ""}, inplace=True)
    return export_dataframe

def TeamStatPull(team):
    batting, test = StatPullBatting(team, "test")  
    pitching, test = StatPullPitching(team, "test")  
    fielding, test = StatPullFielding(team, "test")
    return batting, pitching, fielding


def SaveJSON(data, filestring):
    with open(str(filestring + ".json"), 'w') as jsonfile:
        json.dump(data, jsonfile)

def _get_stat_dict(obj):
    """Get dict representation, using to_dict() if available."""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    return obj.__dict__


def StatSaverCSV(objects, filename):
    with open(str(filename + ".csv"), 'w', newline='') as csvfile:
        first_dict = _get_stat_dict(objects[0])
        writer = csv.DictWriter(csvfile, fieldnames=first_dict.keys())
        writer.writeheader()
        for obj in objects:
            writer.writerow(_get_stat_dict(obj))


def StatSaverJSON(objects, filename):
    with open(str(filename + ".json"), 'w') as jsonfile:
        json.dump([_get_stat_dict(obj) for obj in objects], jsonfile)
        
def StatSaverCombo(objects, filename):
    StatSaverCSV(objects, filename)
    StatSaverJSON(objects, filename)

def GameJSONCombiner(resultdict):
    battingstats = BatJSONCombiner(resultdict)
    pitchingstats = PitchJSONCombiner(resultdict)
    fieldingstats = FieldJSONCombiner(resultdict)
    resultsstats = ResultsJSONCombiner(resultdict)

    fullexport = {
        "results": [result.__dict__ for result in resultsstats],
        "stats": {
            "batting": [player.__dict__ for player in battingstats],
            "pitching": [player.__dict__ for player in pitchingstats],
            "fielding": [player.__dict__ for player in fieldingstats]
        }
    }

    return fullexport

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
        print(fielder.__dict__)
    return fielders

def ResultsJSONCombiner(resultdict):
    results = []
    for game in resultdict.values():
        result = game['result']
        result_obj = SCObject(**result)
        results.append(result_obj)
    for result in results:
        print(result.__dict__)
    return results




class SCObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def PitchDeDuper(players):
    result = {}
    for player in players:
        if player.pid in result:
            result[player.pid].win += player.win
            result[player.pid].loss += player.loss
            result[player.pid].earned_runs += player.earned_runs
            result[player.pid].unearned_runs += player.unearned_runs
            # Convert display innings to outs, add, then back to display
            existing_outs = innings_to_outs(result[player.pid].innings_pitched)
            new_outs = innings_to_outs(player.innings_pitched)
            result[player.pid].innings_pitched = outs_to_innings(existing_outs + new_outs)
            result[player.pid].pitches_thrown += player.pitches_thrown
            result[player.pid].balls += player.balls
            result[player.pid].strikes += player.strikes
            result[player.pid].walks += player.walks
            result[player.pid].strikeouts += player.strikeouts
            result[player.pid].homeruns += player.homeruns
            result[player.pid].triples += player.triples
            result[player.pid].doubles += player.doubles
            result[player.pid].singles += player.singles
            result[player.pid].hbp += player.hbp
            result[player.pid].ibb += player.ibb
            result[player.pid].wildpitches += player.wildpitches
            result[player.pid].balks += player.balks
            result[player.pid].games_started += player.games_started
            result[player.pid].appearances += player.appearances
            # Expanded stats
            result[player.pid].batters_faced += getattr(player, 'batters_faced', 0)
            result[player.pid].sacrifice_flies_allowed += getattr(player, 'sacrifice_flies_allowed', 0)
            result[player.pid].gidp_induced += getattr(player, 'gidp_induced', 0)
            result[player.pid].ground_balls_allowed += getattr(player, 'ground_balls_allowed', 0)
            result[player.pid].fly_balls_allowed += getattr(player, 'fly_balls_allowed', 0)
            result[player.pid].popups_allowed += getattr(player, 'popups_allowed', 0)
            result[player.pid].inherited_runners += getattr(player, 'inherited_runners', 0)
            result[player.pid].inherited_runners_scored += getattr(player, 'inherited_runners_scored', 0)
            result[player.pid].contact_barrel += getattr(player, 'contact_barrel', 0)
            result[player.pid].contact_solid += getattr(player, 'contact_solid', 0)
            result[player.pid].contact_flare += getattr(player, 'contact_flare', 0)
            result[player.pid].contact_burner += getattr(player, 'contact_burner', 0)
            result[player.pid].contact_under += getattr(player, 'contact_under', 0)
            result[player.pid].contact_topped += getattr(player, 'contact_topped', 0)
            result[player.pid].contact_weak += getattr(player, 'contact_weak', 0)

        else:
            result[player.pid] = player
    return list(result.values())

def FieldDeDuper(players):
    result = {}
    for player in players:
        if player.pid in result:
            result[player.pid].throwing_errors += player.throwing_errors
            result[player.pid].catching_errors += player.catching_errors
            result[player.pid].assists += player.assists
            result[player.pid].putouts += player.putouts
            result[player.pid].double_plays_turned += getattr(player, 'double_plays_turned', 0)
            # Convert display innings to outs, add, then back to display
            existing_outs = innings_to_outs(result[player.pid].innings_played)
            new_outs = innings_to_outs(player.innings_played)
            result[player.pid].innings_played = outs_to_innings(existing_outs + new_outs)

        else:
            result[player.pid] = player
    return list(result.values())

#def ResultsDeDuper(results):
#    return results

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
            # Expanded stats
            result[player.pid].sacrifice_flies += getattr(player, 'sacrifice_flies', 0)
            result[player.pid].gidp += getattr(player, 'gidp', 0)
            result[player.pid].ground_balls += getattr(player, 'ground_balls', 0)
            result[player.pid].fly_balls += getattr(player, 'fly_balls', 0)
            result[player.pid].popups += getattr(player, 'popups', 0)
            result[player.pid].contact_barrel += getattr(player, 'contact_barrel', 0)
            result[player.pid].contact_solid += getattr(player, 'contact_solid', 0)
            result[player.pid].contact_flare += getattr(player, 'contact_flare', 0)
            result[player.pid].contact_burner += getattr(player, 'contact_burner', 0)
            result[player.pid].contact_under += getattr(player, 'contact_under', 0)
            result[player.pid].contact_topped += getattr(player, 'contact_topped', 0)
            result[player.pid].contact_weak += getattr(player, 'contact_weak', 0)

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

def JSONCombinePitch(pitchstats):
        # Convert display innings (9.1) to actual innings (9.333) for rate calculations
        outs = innings_to_outs(pitchstats.innings_pitched)
        actual_innings = outs / 3 if outs > 0 else 1
        pitchstats.era = round((9 * pitchstats.earned_runs / actual_innings), 3)
        pitchstats.hits_allowed = (pitchstats.singles + pitchstats.doubles + pitchstats.triples + pitchstats.homeruns)
        pitchstats.whip = round(((pitchstats.walks + pitchstats.hits_allowed) / actual_innings), 3)
        pitchstats.fip = round((((13 * pitchstats.homeruns) + (3 * (pitchstats.walks + pitchstats.hbp)) - (2 * pitchstats.strikeouts)) / actual_innings), 3)

def JSONCombineField(fieldstats):
        fieldstats.errors = fieldstats.throwing_errors + fieldstats.catching_errors
        fieldstats.defensive_chances = fieldstats.putouts + fieldstats.assists + fieldstats.errors
        if fieldstats.defensive_chances == 0:
            fieldstats.fielding_percentage = None
        else:
            fieldstats.fielding_percentage = round(((fieldstats.putouts+fieldstats.assists) / fieldstats.defensive_chances), 3)

def BatchStatSaverCSV(objects, filename):
    with open(str(filename+".csv"), 'w', newline='') as csvfile:
      
        fieldnames = objects[0].keys()

        print(fieldnames)

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for object in objects:
            writer.writerow(object)
