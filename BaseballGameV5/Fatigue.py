import math

def TickEnergy(baseline, player):
    max = 3.16227766
    mod = player.pendurance / 50
    energy_mod = (1-mod) * baseline.energytickcap
    calcedenergystep = baseline.energystep + energy_mod
    player.energy = player.energy - (player.energy*(calcedenergystep*.01))
    player.abilitymodifierscore = (math.sqrt(math.sqrt(player.energy))/max)


def TickBatterEnergy(player):
    max = 3.16227766
    player.energy = player.energy - 1.0
    if player.energy < 0:
        player.energy = 0
    player.abilitymodifierscore = (math.sqrt(math.sqrt(player.energy))/max)

def TickDefenderEnergy(player):
    max = 3.16227766
    player.energy = player.energy - 0.35
    if player.energy < 0:
        player.energy = 0
    player.abilitymodifierscore = (math.sqrt(math.sqrt(player.energy))/max)

def Injury():
    pass
