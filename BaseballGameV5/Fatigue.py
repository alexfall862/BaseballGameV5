import math

def TickEnergy(baseline, player):
    max = 3.16227766
    mod = player.pendurance / 50
    energy_mod = (1-mod) * baseline.energytickcap
    calcedenergystep = baseline.energystep + energy_mod
    player.energy = player.energy - (player.energy*(calcedenergystep*.01))
    player.abilitymodifierscore = 1 #(math.sqrt(math.sqrt(player.energy))/max)


def Injury():
    pass
