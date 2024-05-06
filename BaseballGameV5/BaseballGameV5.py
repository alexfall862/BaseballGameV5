import Game as Game
import Lineup as Line
import Roster as Rost
import Action as Act
import Batch as b
import Player as p


rules = "MLB"

directory = f"..\\Game"
#print(directory)

k = p.loadjsonroster('TestRoster')

print(k[0])

exit() 

x = b.Batch(directory, rules)

for matchup in x.listofgames:
    print(Game.Game(matchup))
