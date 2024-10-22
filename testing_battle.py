from math import inf  # noqa

from Battle import Army, Battle, Landscape, Stance
from GraphicBattle import GraphicBattle
from Data import smooth, even, rough, broken, ragged, forest, river, PresetLandscapes, \
                 spear, sword, pike, irreg, javelin, archer, h_horse, l_horse  # noqa

graphical = False


def preamble():
    return Army("Army 1", Stance.LINE, "DarkBlue"), Army("Army 2", Stance.LINE, "DarkRed")


def do_single_terrain_battle(army_1, army_2, terrain, name="testing_out"):
    files = set(army_1.file_units) | set(army_2.file_units)
    landscape = Landscape({file: {inf: terrain} for file in files})
    if graphical:
        GraphicBattle(army_1, army_2, landscape, (1080, 720), name).do(10)
    else:
        Battle(army_1, army_2, landscape).do(10)


""" spear - sword - pike trichotomy """


def test_A1():
    # spears win on even, swords win on rough
    army_1, army_2 = preamble()
    army_1.add(0, spear)
    army_2.add(0, sword)
    do_single_terrain_battle(army_1, army_2, even)


def test_A2():
    # spears win on rough, swords win on broken
    army_1, army_2 = preamble()
    army_1.add(-1, spear).add(0, spear).add(1, spear)
    army_2.add(-1, sword).add(0, sword).add(1, sword)
    do_single_terrain_battle(army_1, army_2, broken)


def test_A3():
    # pikes win on even, spears win on rough
    army_1, army_2 = preamble()
    army_1.add(0, spear)
    army_2.add(0, pike)
    do_single_terrain_battle(army_1, army_2, rough)


def test_A4():
    # pikes win on rough, spears win on broken
    army_1, army_2 = preamble()
    army_1.add(-1, spear).add(0, spear).add(1, spear)
    army_2.add(-1, pike).add(0, pike).add(1, pike)
    do_single_terrain_battle(army_1, army_2, broken)


def test_A5():
    # pikes win on even, swords win on rough
    army_1, army_2 = preamble()
    army_1.add(0, sword)
    army_2.add(0, pike)
    do_single_terrain_battle(army_1, army_2, even)


def test_A6():
    # pikes win on rough, swords win on broken
    army_1, army_2 = preamble()
    army_1.add(-1, sword).add(0, sword).add(1, sword)
    army_2.add(-1, pike).add(0, pike).add(1, pike)
    do_single_terrain_battle(army_1, army_2, rough)


""" Adding in ranged units to the mix """


def test_B1():
    # spears win on rough, javelins win on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, rough)


def test_B2():
    # spears broken, javelins win on ragged
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-2, javelin).add(-1, javelin).add(0, javelin).add(1, javelin).add(2, javelin)
    do_single_terrain_battle(army_1, army_2, ragged)


def test_B3():
    # sword win on broken, javelins win on ragged
    army_1, army_2 = preamble()
    army_1.add(0, sword).add(1, sword)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, broken)


def test_B4():
    # pikes win on rough, javelins on broken
    army_1, army_2 = preamble()
    army_1.add(0, pike).add(1, pike)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, broken)


def test_B5():
    # javelins win on everything but river (deliberate, archers are better in mixed armies)
    army_1, army_2 = preamble()
    army_1.add(0, javelin).add(1, javelin)
    army_2.add(0, archer).add(1, archer)
    do_single_terrain_battle(army_1, army_2, river)


def test_B6():
    # spears win on rough, archers win on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, archer).add(1, archer)
    do_single_terrain_battle(army_1, army_2, rough)


def test_B7():
    # spears win on rough, irregs win on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, irreg).add(1, irreg)
    do_single_terrain_battle(army_1, army_2, rough)


def test_B8():
    # swords win on broken, irregs win on ragged
    army_1, army_2 = preamble()
    army_1.add(0, sword).add(1, sword)
    army_2.add(0, irreg).add(1, irreg)
    do_single_terrain_battle(army_1, army_2, broken)


def test_B9():
    # irregs win on rough, javelins win on broken
    army_1, army_2 = preamble()
    army_1.add(0, javelin).add(1, javelin)
    army_2.add(0, irreg).add(1, irreg)
    do_single_terrain_battle(army_1, army_2, broken)


""" Adding in cavalry units to the mix """


def test_C1():
    # h_horse wins on even, spear wins on rough
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, h_horse).add(1, h_horse)
    do_single_terrain_battle(army_1, army_2, even)


def test_C2():
    # h_horse wins on rough, spear wins in broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(1, h_horse).add(2, h_horse)  # NOTE DELIBERATE OFFSET
    do_single_terrain_battle(army_1, army_2, rough)


def test_C3():
    # Horses win on smooth, lose on even
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, l_horse).add(1, l_horse)
    do_single_terrain_battle(army_1, army_2, even)


def test_C4():
    # heavy wins on even, light on broken
    army_1, army_2 = preamble()
    army_1.add(0, h_horse).add(1, h_horse)
    army_2.add(1, l_horse).add(2, l_horse)  # NOTE DELIBERATE OFFSET
    do_single_terrain_battle(army_1, army_2, even)


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
    # 3+2 loses to 5+0 when deployed in the centre, but wins at the edge for spears and swords
    x = pike
    army_1, army_2 = preamble()
    army_1.add(-2, x).add(-1, x).add(0, x).add(1, x).add(2, x)
    army_2.add(-1, x).add(0, x).add(-2, x).add_reserves(x, x)
    do_single_terrain_battle(army_1, army_2, even)


def test_D4():
    # 4+1 beat 5+0 and 3+2 (no matter where it's deployed) for spears and swords, but not pikes
    x = sword
    army_1, army_2 = preamble()
    army_1.add(-2, x).add(-1, x).add(0, x).add(1, x).add(2, x)
    army_2.add(-2, x).add(-1, x).add(0, x).add(1, x).add_reserves(x)
    do_single_terrain_battle(army_1, army_2, even)


""" Testing how many weak units are needed to defeat a strong one """


def test_E1():
    # Militia power so that they just lose
    from Battle import UnitType
    militia = UnitType("Militia", 177)  # -113

    army_1, army_2 = preamble()
    army_1.add(0, sword)
    army_2.add(0, militia).add(1, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_E2():
    # Militia power so that they just lose
    from Battle import UnitType
    militia = UnitType("Militia", 208)  # -82

    army_1, army_2 = preamble()
    army_1.add(-1, sword).add(0, sword).add(1, sword)
    army_2.add(-2, militia).add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_E3():
    # Militia power so that they just lose
    from Battle import UnitType
    militia = UnitType("Militia", 217)  # -103

    army_1, army_2 = preamble()
    army_1.add(-1, pike).add(0, pike).add(1, pike)
    army_2.add(-2, militia).add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_E4():
    # Militia power so that they just lose
    from Battle import UnitType
    militia = UnitType("P Militia", 221, 0.6)  # -99

    army_1, army_2 = preamble()
    army_1.add(-1, pike).add(0, pike).add(1, pike)
    army_2.add(-2, militia).add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    do_single_terrain_battle(army_1, army_2, even)


""" Testing height """


def test_F1():
    # Minimum height for militia to make up for 30 power disadvantage
    from Battle import UnitType
    militia = UnitType("Militia", 260)

    army_1, army_2 = preamble()
    army_1.add(0, militia)
    army_2.add(0, sword)
    terrain = {0: {inf: even}}
    height = {(0, -4): 6.1, (0, 4): 0}
    landscape = Landscape(terrain, height)
    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(10)


def test_F2():
    # Army_1 wins with height map, just loses without it
    # Also check that contours are drawn properly
    army_1, army_2 = preamble()

    army_1.add(-2, archer).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    army_1.add_reserves(h_horse)
    army_2.add(-2, javelin).add(-1, pike).add(0, pike).add(1, pike).add(2, spear)
    army_2.add_reserves(irreg)

    terrain = {-2: {-2: broken, 3: rough, inf: rough},
               -1: {-1: rough, inf: even},
               0: {-3: rough, 2: even, inf: smooth},
               1: {-1: rough, 4: even, inf: smooth},
               2: {-2: even, inf: smooth}}
    height = {(-0.5, -4): 5,
              (0.5, -4): 4,
              (0, 4): 0,
              (-1.45, 2): -1,
              (1.45, 2): -1}
    landscape = Landscape(terrain, height)

    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(verbosity=10)


""" Testing Stances"""


def utils_for_G_tests(stance_1: Stance, stance_2: Stance):
    army_1 = Army("1", stance_1, "DarkBlue")
    army_1.add(-2, archer).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    army_1.add_reserves(h_horse)

    army_2 = Army("2", stance_2, "DarkRed")
    army_2.add(-2, javelin).add(-1, pike).add(0, pike).add(1, pike).add(2, pike)
    army_2.add_reserves(l_horse)

    ter = {file: {-4: even, -2: rough, -0.75: broken, 0.75: river, 2: broken, 4: rough, inf: even}
           for file in range(-2, 3)}

    return army_1, army_2, ter


def test_G1():
    # Check FAST looks reasonable
    army_1, army_2, terrain = utils_for_G_tests(Stance.FAST, Stance.LINE)
    army_1.add(2, h_horse)
    landscape = Landscape(terrain, {})
    GraphicBattle(army_2, army_1, landscape, (1080, 720), "testing_out").do(10)


def test_G2():
    # Check it looks good for all combinations of HOLD, and LINE
    army_1, army_2, terrain = utils_for_G_tests(Stance.LINE, Stance.LINE)
    landscape = Landscape(terrain, {})
    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(10)


def test_G3():
    # Check it looks good for all combinations of HOLD, and LINE
    army_1, army_2, terrain = utils_for_G_tests(Stance.HOLD, Stance.LINE)

    height = {(2.2, 0): -3,
              (0.9, 0): -3,
              (0, 0): -3,
              (-0.9, 0): -3,
              (-2.2, 0): -3,
              (-1.2, 7.5): 3,
              (1.6, 6.5): 2,
              (-1.6, -7.5): 0,
              (1.2, -6.5): 3}
    landscape = Landscape(terrain, height)
    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(10)


def test_G4():
    # Check it looks good for all combinations of HOLD, and LINE
    army_1, army_2, terrain = utils_for_G_tests(Stance.LINE, Stance.HOLD)

    height = {(2.2, 0): -3,
              (0.9, 0): -3,
              (0, 0): -3,
              (-0.9, 0): -3,
              (-2.2, 0): -3,
              (-1.2, 7.5): 5,
              (1.6, 6.5): 0,
              (-1.6, -7.5): 0,
              (1.2, -6.5): 5}
    landscape = Landscape(terrain, height)
    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(10)


test_G4()
