import Game as Game
import Lineup as Line
import Roster as Rost
import Action as Act
import Batch as b
import Player as p
import Stats as stats
import DatabaseImporter as dbimp

db = dbimp.InitializeDB()



data = db.pullteam("NYY")
print(data)
exit()

rules = "MLB"

directory = f"..\\Game"

games = b.Batch(directory, rules)

dictofresults = {}
listofresults = []
for game in games.listofgames:
    currentgame = Game.Game(game)
    currentgame.RunGame()
    dictofresults[f"{currentgame.gname}"] = currentgame.ReturnBox()

stats.SaveJSON(dictofresults, "batch_testexport")
stats.GameJSONCombiner(dictofresults)
    




