import math

def TickEnergy(baseline, player):
    max = 3.16227766
    #player.energy = player.energy - baseline.energytickcap
    mod = player.pendurance / 50
    energy_mod = (1-mod) * baseline.energytickcap
    calcedenergystep = baseline.energystep + energy_mod
    #print(f"Stamina Calc: {player.name} {player.energy} {baseline.energystep} {player.pendurance} {mod} {energy_mod} {calcedenergystep}")
    player.energy = player.energy - (player.energy*(calcedenergystep*.01))
    player.abilitymodifierscore = 1# (math.sqrt(math.sqrt(player.energy))/max)
    #print(f"Attribute Check: {player.pthrowpower} Mod Score: {player.abilitymodifierscore}")

def Injury():
    pass
