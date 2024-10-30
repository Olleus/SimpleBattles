from math import inf

from Battle import Battle
from Data import smooth, even, rough, broken, ragged, forest, river, PresetLandscapes, \
                 line, light, grenadier, cannon, cuirassier, hussar, tribesmen  # noqa
from Geography import Landscape
from Globals import Stance
from GraphicBattle import GraphicBattle
from Unit import Army

graphical = True


def preamble():
    return Army("Army 1", Stance.BAL, "DarkBlue"), Army("Army 2", Stance.BAL, "DarkRed")


def do_single_terrain_battle(army_1, army_2, terrain, name="modern_out"):
    files = set(army_1.file_units) | set(army_2.file_units)
    landscape = Landscape({file: {inf: terrain} for file in files})
    if graphical:
        GraphicBattle(army_1, army_2, landscape, 800, name).do(10)
    else:
        Battle(army_1, army_2, landscape).do(10)


""" Infantry trichotomy """


def test_A1():
    # Morale should be <70% by the time melee combat starts
    army_1, army_2 = preamble()
    army_1.stance = Stance.AGG
    army_1.add(0, line)
    army_2.add(0, line)
    do_single_terrain_battle(army_1, army_2, even)


def test_A2():
    # Line wins on even, loses on rough
    army_1, army_2 = preamble()
    army_1.add(0, line)
    army_2.add(0, light)
    do_single_terrain_battle(army_1, army_2, even)


def test_A3():
    # Grenadier wins on even, loses on rough (or when DEF)
    army_1, army_2 = preamble()
    army_1.stance = Stance.BAL
    army_1.add(0, grenadier)
    army_2.add(0, line)
    do_single_terrain_battle(army_1, army_2, even)


def test_A4():
    # Grenadier wins on rough, loses on broken
    army_1, army_2 = preamble()
    army_1.add(0, grenadier)
    army_2.add(0, light)
    do_single_terrain_battle(army_1, army_2, rough)


""" Others """


def test_B1():
    # Cannon loses to all infantry, except when infantry is DEF
    army_1, army_2 = preamble()
    army_1.stance = Stance.BAL
    army_1.add(0, grenadier)  # Line, light, grenadier
    army_2.add(0, cannon)
    do_single_terrain_battle(army_1, army_2, even)


def test_C1():
    # Cuirassier wins on smooth, loses otherwise
    army_1, army_2 = preamble()
    army_1.add(0, cuirassier)
    army_2.add(0, line)
    do_single_terrain_battle(army_1, army_2, smooth)


def test_C2():
    # Cuirassier always loses (advantage is in speed)
    army_1, army_2 = preamble()
    army_1.add(0, cuirassier)
    army_2.add(0, grenadier)
    do_single_terrain_battle(army_1, army_2, rough)


def test_C3():
    # Cuirassier wins on rough, loses on broken
    army_1, army_2 = preamble()
    army_1.add(0, cuirassier)
    army_2.add(0, light)
    do_single_terrain_battle(army_1, army_2, broken)


def test_C4():
    # Cuirassier wins on rough, loses on broken
    army_1, army_2 = preamble()
    army_1.add(0, cuirassier)
    army_2.add(0, cannon)
    do_single_terrain_battle(army_1, army_2, broken)


def test_D1():
    # Hussar wins on broken, loses on ragged
    army_1, army_2 = preamble()
    army_1.add(0, hussar)
    army_2.add(0, cannon)
    do_single_terrain_battle(army_1, army_2, broken)


def test_D2():
    # Wins on broken, loses on ragged
    army_1, army_2 = preamble()
    army_1.add(0, hussar)
    army_2.add(0, light)
    do_single_terrain_battle(army_1, army_2, broken)


def test_D3():
    # Hussar's lose on everything
    army_1, army_2 = preamble()
    army_1.add(0, hussar).add(1, hussar).add(2, hussar)
    army_2.add(0, line).add(1, line).add(2, line)
    do_single_terrain_battle(army_1, army_2, broken)


def test_D4():
    # Hussar's win due to pursuing damage
    army_1, army_2 = preamble()
    army_1.add(0, hussar).add(1, hussar).add(2, hussar)
    army_2.add(-2, grenadier).add(-1, grenadier).add(0, grenadier)
    do_single_terrain_battle(army_1, army_2, smooth)


def test_E1():
    # 3 Tribesmen win, 2 lose
    army_1, army_2 = preamble()
    army_1.add(-1, tribesmen).add(0, tribesmen)
    army_2.add(0, line)
    do_single_terrain_battle(army_1, army_2, even)


def test_E2():
    # Tribesmen lose with 1 reserve, win with 2
    army_1, army_2 = preamble()
    army_2.stance = Stance.DEF
    army_1.add(-2, tribesmen).add(-1, tribesmen).add(0, tribesmen)
    army_1.add(1, tribesmen).add(2, tribesmen)
    army_1.add_reserves(tribesmen, tribesmen)
    army_2.add(-1, light).add(0, cannon).add(1, light)
    do_single_terrain_battle(army_1, army_2, rough)  # Note - not even


test_E2()
