from math import inf  # noqa

from Battle import Stance, Army, Landscape
from GraphicBattle import GraphicBattle
from Data import smooth, even, rough, broken, ragged, forest, river, PresetLandscapes, \
                 spear, sword, pike, javelin, archer, h_horse, l_horse, irreg  # noqa


def preamble():
    return Army("1", Stance.LINE, "DarkBlue"), Army("2", Stance.LINE, "DarkRed")


def do_single_terrain_battle(army_1, army_2, terrain, name="testing_out"):
    files = set(army_1.file_units) | set(army_2.file_units)
    landscape = Landscape({file: {inf: terrain} for file in files})
    GraphicBattle(army_1, army_2, landscape, (1080, 640), name).do(10)


""" spear - sword - pike trichotomy """


def test_A1():
    # spears win on smooth, swords win on even
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, sword).add(1, sword)
    do_single_terrain_battle(army_1, army_2, even)


def test_A2():
    # spears win on even, swords win on rough
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    do_single_terrain_battle(army_1, army_2, even)


def test_A3():
    # pikes win on rough, spears win on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, pike).add(1, pike)
    do_single_terrain_battle(army_1, army_2, broken)


def test_A4():
    # pikes win on rough, spears win on broken
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-2, pike).add(-1, pike).add(0, pike).add(1, pike).add(2, pike)
    do_single_terrain_battle(army_1, army_2, broken)


def test_A5():
    # pikes win on even, swords win on rough
    army_1, army_2 = preamble()
    army_1.add(0, sword).add(1, sword)
    army_2.add(0, pike).add(1, pike)
    do_single_terrain_battle(army_1, army_2, rough)


def test_A6():
    # pikes win on rough, swords win on broken
    army_1, army_2 = preamble()
    army_1.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    army_2.add(-2, pike).add(-1, pike).add(0, pike).add(1, pike).add(2, pike)
    do_single_terrain_battle(army_1, army_2, broken)


""" Adding in ranged units to the mix """


def test_B1():
    # spears win on even, javelins win on rough
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, rough)


def test_B2():
    # spears win on rough, javelins win on broken
    army_1, army_2 = preamble()
    army_1.add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-1, javelin).add(0, javelin).add(1, javelin).add(2, javelin)
    do_single_terrain_battle(army_1, army_2, broken)


def test_B3():
    # sword win on rough, javelins win on broken
    army_1, army_2 = preamble()
    army_1.add(0, sword).add(1, sword)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, broken)


def test_B4():
    # pikes win on even, javelins on rough
    army_1, army_2 = preamble()
    army_1.add(0, pike).add(1, pike)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, even)


def test_B5():
    # javelins win on rough, archers win on broken
    army_1, army_2 = preamble()
    army_1.add(0, javelin).add(1, javelin)
    army_2.add(0, archer).add(1, archer)
    do_single_terrain_battle(army_1, army_2, broken)


def test_B6():
    # spears win with 2 files, archers win with 1
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, archer).add(1, archer)
    do_single_terrain_battle(army_1, army_2, even)


def test_B7():
    # spears win on rough, irregs win on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, irreg).add(1, irreg)
    do_single_terrain_battle(army_1, army_2, rough)


def test_B8():
    # irregs win on even, javelins win on broken
    army_1, army_2 = preamble()
    army_1.add(0, javelin).add(1, javelin)
    army_2.add(0, irreg).add(1, irreg)
    do_single_terrain_battle(army_1, army_2, even)


""" Adding in cavalry units to the mix """


def test_C1():
    # h_horse wins on even, spear wins on rough
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, h_horse).add(1, h_horse)
    do_single_terrain_battle(army_1, army_2, rough)


def test_C2():
    # horse-army wins on ragged, loses on forest
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(1, h_horse).add(2, h_horse)
    do_single_terrain_battle(army_1, army_2, forest)


def test_C3():
    # l_horse win when 1v1, spears win when 2v2
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, l_horse).add(1, l_horse)
    do_single_terrain_battle(army_1, army_2, rough)


def test_C4():
    # light win when 1v1, heavy wins when 2v2
    army_1, army_2 = preamble()
    army_1.add(0, h_horse).add(1, h_horse)
    army_2.add(0, l_horse).add(1, l_horse)
    do_single_terrain_battle(army_1, army_2, smooth)


""" Checking reserves work as intended """


def test_D1():
    # Reserves come in at the correct time and all is displayed as expected
    army_1, army_2 = preamble()
    army_1.add(0, pike).add_reserves(pike, pike, pike)
    army_2.add(0, sword).add_reserves(sword, sword, sword)
    do_single_terrain_battle(army_1, army_2, rough)


def test_D2():
    # Side with reserves wins (in a very artificial scenario)
    army_1, army_2 = preamble()
    army_1.add(-2, sword).add(-1, sword).add(0, sword).add_reserves(h_horse)
    army_2.add(-2, sword).add(-1, sword).add(0, sword).add(1, h_horse)

    landscape = Landscape({-2: {inf: smooth},
                           -1: {inf: smooth},
                           0: {inf: smooth},
                           1: {inf: river}})

    GraphicBattle(army_1, army_2, landscape, (720, 480), "testing_out").do(verbosity=10)


def test_D3():
    # 3+2 loses to 5+0 when deployed in the centre, but wins when deployed at the edge
    army_1, army_2 = preamble()
    army_1.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    army_2.add(-1, sword).add(0, sword).add(-2, sword).add_reserves(sword, sword)
    do_single_terrain_battle(army_1, army_2, even)


def test_D4():
    # 4+1 beat 5+0 and 3+2 (no matter where it's deployed)
    army_1, army_2 = preamble()
    army_1.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    army_2.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add_reserves(sword)
    do_single_terrain_battle(army_1, army_2, even)


""" Testing how many weak units are needed to defeat a strong one """


def test_E1():
    # Militia power so that they just lose
    from Battle import UnitType
    militia = UnitType("Militia", 190)

    army_1, army_2 = preamble()
    army_1.add(0, sword)
    army_2.add(0, militia).add(1, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_E2():
    # Militia power so that they just lose
    from Battle import UnitType
    militia = UnitType("Militia", 227)

    army_1, army_2 = preamble()
    army_1.add(-1, sword).add(0, sword).add(1, sword)
    army_2.add(-2, militia).add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    do_single_terrain_battle(army_1, army_2, even)


""" Testing height """


def test_F1():
    # Minimum height for militia to make up for 40 power disadvantage
    from Battle import UnitType
    militia = UnitType("Militia", 260)

    army_1, army_2 = preamble()
    army_1.add(0, militia)
    army_2.add(0, sword)
    terrain = {0: {inf: even}}
    height = {(0, -4): 8.2, (0, 4): 0}
    landscape = Landscape(terrain, height)
    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(10)


def test_F2():
    # Army_1 wins with height map, loses if it's removed
    # Also check that contours are drawn properly
    army_1, army_2 = preamble()

    army_1.add(-2, archer).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    army_1.add_reserves(h_horse)
    army_2.add(-2, javelin).add(-1, spear).add(0, pike).add(1, pike).add(2, pike)
    army_2.add_reserves(h_horse)

    terrain = {-2: {-3: broken, 1: rough, inf: rough},
               -1: {-2: rough, inf: even},
               0: {-4: rough, 0: even, inf: smooth},
               1: {-2: rough, 2: even, inf: smooth},
               2: {-3: even, inf: smooth}}
    height = {(-0.5, -3): 4,
              (0.5, -3): 3,
              (0, 4): 1,
              (-1.75, 2): 0,
              (1.75, 2): 0}
    landscape = Landscape(terrain, height)

    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(verbosity=10)


test_F2()

# TODO: REDO ALL TESTS NOW THAT GLOBALS HAVE CHANGED
