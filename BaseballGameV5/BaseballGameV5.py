import Game as Game
import Lineup as Line
import Roster as Rost
import Action as Act
import Batch as b


rules = "MLB"

directory = f"..\\Game"
#print(directory)

x = b.Batch(directory, rules)

for matchup in x.listofgames:
    print(Game.Game(matchup))
