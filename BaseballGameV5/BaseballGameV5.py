import Game as Game
import Lineup as Line
import Roster as Rost
import Action as Act
import Batch as b
import Player as p


rules = "MLB"

directory = f"..\\Game"

games = b.Batch(directory, rules)

for game in games.listofgames:
    currentgame = Game.Game(game)
    print(currentgame)



