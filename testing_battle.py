from math import inf

from Battle import Battle
from Data import smooth, even, rough, broken, ragged, forest, river, PresetLandscapes, \
                 spear, sword, pike, irreg, javelin, archer, mixed, h_horse, l_horse  # noqa
from Geography import Landscape
from Globals import Stance
from GraphicBattle import GraphicBattle
from Unit import Army

graphical = True


def preamble():
    return Army("Army 1", Stance.BAL, "DarkBlue"), Army("Army 2", Stance.BAL, "DarkRed")


def do_single_terrain_battle(army_1, army_2, terrain, name="testing_out"):
    files = set(army_1.file_units) | set(army_2.file_units)
    landscape = Landscape({file: {inf: terrain} for file in files})
    if graphical:
        GraphicBattle(army_1, army_2, landscape, 920, name).do(10)
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
    do_single_terrain_battle(army_1, army_2, broken)


def test_B3():
    # sword win on broken, javelins win on ragged
    army_1, army_2 = preamble()
    army_1.add(0, sword).add(1, sword)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, ragged)


def test_B4():
    # pikes win on rough, javelins on broken
    army_1, army_2 = preamble()
    army_1.add(0, pike).add(1, pike)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, rough)


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
    do_single_terrain_battle(army_1, army_2, broken)


def test_B7():
    # spears win on rough, irregs win on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, irreg).add(1, irreg)
    do_single_terrain_battle(army_1, army_2, rough)


def test_B8():
    # swords win on broken, irregs win on ragged
    army_1, army_2 = preamble()
    army_1.add(-1, sword).add(0, sword).add(1, sword)
    army_2.add(-1, irreg).add(0, irreg).add(1, irreg)
    do_single_terrain_battle(army_1, army_2, ragged)


""" Adding in mixed units """


def test_C1():
    # spear wins on rough, loses on broken. Mixed unit never closes in, pushing stays at melee
    army_1, army_2 = preamble()
    army_1.add(0, spear)
    army_2.add(0, mixed)
    do_single_terrain_battle(army_1, army_2, rough)


def test_C1b():
    # Mixed unit does close in, pushing stays at melee
    army_1, army_2 = preamble()
    army_2.stance = Stance.AGG
    army_1.add(0, spear)
    army_2.add(0, mixed)
    do_single_terrain_battle(army_1, army_2, rough)


def test_C2():
    # mixed wins on even, archer wins on rough. Mixed unit always closes in, pushing stays at melee
    army_1, army_2 = preamble()
    army_1.add(0, archer).add(1, archer)
    army_2.add(0, mixed).add(1, mixed)
    do_single_terrain_battle(army_1, army_2, even)


def test_C2b():
    # Mixed unit does not close in, pushing stays at range
    army_1, army_2 = preamble()
    army_2.stance = Stance.DEF
    army_1.add(0, archer)
    army_2.add(0, mixed)
    do_single_terrain_battle(army_1, army_2, rough)


def test_C3():
    # Neither unit closes in, pushing stays at range
    army_1, army_2 = preamble()
    army_1.add(0, mixed)
    army_2.add(0, mixed)
    do_single_terrain_battle(army_1, army_2, rough)


def test_C4():
    # Both units close in, pushing stays at melee
    army_1, army_2 = preamble()
    army_1.add(0, mixed)
    army_2.add(1, mixed)  # Note Offset
    do_single_terrain_battle(army_1, army_2, rough)


""" Adding in cavalry units to the mix """


def test_D1():
    # h_horse wins on even, spear wins on rough
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, h_horse).add(1, h_horse)
    do_single_terrain_battle(army_1, army_2, rough)


def test_D2():
    # h_horse wins on smooth, pike wins on even
    army_1, army_2 = preamble()
    army_1.add(0, pike)
    army_2.add(0, h_horse)
    do_single_terrain_battle(army_1, army_2, smooth)


def test_D3():
    # Horses win on smooth, lose on even
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, l_horse).add(1, l_horse)
    do_single_terrain_battle(army_1, army_2, smooth)


def test_D4():
    # shock wins on broken, light on ragged
    army_1, army_2 = preamble()
    army_1.add(0, h_horse).add(1, h_horse)
    army_2.add(1, l_horse).add(2, l_horse)  # NOTE DELIBERATE OFFSET
    do_single_terrain_battle(army_1, army_2, ragged)


def test_D5():
    # horses wins on rough, loses on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(1, h_horse).add(2, l_horse)  # NOTE DELIBERATE OFFSET
    do_single_terrain_battle(army_1, army_2, rough)


""" Checking reserves work as intended """


def test_E1():
    # Reserves come in at the correct time and all is displayed as expected
    army_1, army_2 = preamble()
    army_1.add(0, pike).add_reserves(pike, pike, pike)
    army_2.add(0, sword).add_reserves(sword, sword, sword)
    do_single_terrain_battle(army_1, army_2, rough)


def test_E2():
    # Side with reserves wins (in a very artificial scenario)
    army_1, army_2 = preamble()
    army_1.add(-2, sword).add(-1, sword).add(0, sword).add_reserves(h_horse)
    army_2.add(-2, sword).add(-1, sword).add(0, sword).add(1, h_horse)

    landscape = Landscape({-2: {inf: smooth},
                           -1: {inf: smooth},
                           0: {inf: smooth},
                           1: {inf: river}})

    GraphicBattle(army_1, army_2, landscape, 720, "testing_out").do(verbosity=10)


def test_E3():
    # 3+2 loses to 5+0 when deployed in the centre or edge
    x = sword
    army_1, army_2 = preamble()
    army_1.add(-2, x).add(-1, x).add(0, x).add(1, x).add(2, x)
    army_2.add(-1, x).add(0, x).add(-2, x).add_reserves(x, x)
    do_single_terrain_battle(army_1, army_2, even)


def test_E4():
    # 4+1 beat 5+0 for swords and spears, but not pikes or mixed
    x = mixed
    army_1, army_2 = preamble()
    army_1.add(-2, x).add(-1, x).add(0, x).add(1, x).add(2, x)
    army_2.add(-2, x).add(-1, x).add(0, x).add(1, x).add_reserves(x)
    do_single_terrain_battle(army_1, army_2, even)


def test_E5():
    # 4+1 beat 3+2 always
    x = mixed
    army_1, army_2 = preamble()
    army_1.stance = Stance.AGG
    army_1.add(-2, x).add(-1, x).add(0, x).add_reserves(x, x)
    army_2.add(-2, x).add(-1, x).add(0, x).add(1, x).add_reserves(x)
    do_single_terrain_battle(army_1, army_2, even)


test_E4()
""" Testing how many weak units are needed to defeat a strong one """


def test_F1():
    # Militia power so that they just lose
    from Unit import UnitType
    militia = UnitType("Militia", 181)  # -109

    army_1, army_2 = preamble()
    army_1.add(0, sword)
    army_2.add(0, militia).add(1, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_F2():
    # Militia power so that they just lose
    from Unit import UnitType
    militia = UnitType("Militia", 212)  # -78

    army_1, army_2 = preamble()
    army_1.add(-1, sword).add(0, sword).add(1, sword)
    army_2.add(-2, militia).add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_F3():
    # Militia power so that they just lose
    from Unit import UnitType
    militia = UnitType("Militia", 221)  # -99

    army_1, army_2 = preamble()
    army_1.add(-1, pike).add(0, pike).add(1, pike)
    army_2.add(-2, militia).add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_F4():
    # Militia power so that they just lose
    from Unit import UnitType
    militia = UnitType("P Militia", 226, 0.6)  # -94

    army_1, army_2 = preamble()
    army_1.add(-1, pike).add(0, pike).add(1, pike)
    army_2.add(-2, militia).add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    do_single_terrain_battle(army_1, army_2, even)


""" Testing landscape """


def test_G1():
    """Visually check that power changes smoothly with unit movement as intended"""
    army_1, army_2 = preamble()
    army_1.add(0, pike)
    army_2.add(0, javelin)

    terrain = {0: {-2.5: rough, -1.5: broken, -0.5: even, 0: ragged,
                   0.5: smooth, 1: even, 2: forest, 3: river, 4: ragged, inf: even}}
    landscape = Landscape(terrain, {})
    GraphicBattle(army_1, army_2, landscape, 920, "testing_out").do(10)


def test_G2():
    # Minimum height for militia to make up for 30 power disadvantage
    from Unit import UnitType
    militia = UnitType("Militia", 260)

    army_1, army_2 = preamble()
    army_1.add(0, militia)
    army_2.add(0, sword)
    terrain = {0: {inf: even}}
    height = {(0, -4): 6.1, (0, 4): 0}
    landscape = Landscape(terrain, height)
    GraphicBattle(army_1, army_2, landscape, 920, "testing_out").do(10)


def test_G3():
    # Army_1 wins with height map, loses without it
    # Also check that contours are drawn properly
    army_1, army_2 = preamble()

    army_1.add(-2, archer).add(-1, sword).add(0, sword).add(1, sword).add(2, h_horse)
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

    GraphicBattle(army_1, army_2, landscape, 920, "testing_out").do(verbosity=10)


""" Testing Stances"""


def utils_for_H_tests(stance_1: Stance, stance_2: Stance):
    army_1 = Army("1", stance_1, "DarkBlue")
    army_1.add(-2, archer).add(-1, sword).add(0, sword).add(1, sword).add(2, l_horse)
    army_1.add_reserves(h_horse)

    army_2 = Army("2", stance_2, "DarkRed")
    army_2.add(-2, javelin).add(-1, pike).add(0, pike).add(1, pike).add(2, h_horse)
    army_2.add_reserves(l_horse)

    ter = {file: {-4: even, -2: rough, -0.75: broken, 0.75: river, 2: broken, 4: rough, inf: even}
           for file in range(-2, 3)}

    return army_1, army_2, ter


def test_H1():
    # Check all combinations of stances look reasonable
    army_1, army_2, terrain = utils_for_H_tests(Stance.DEF, Stance.DEF)
    landscape = Landscape(terrain, {})
    GraphicBattle(army_1, army_2, landscape, 920, "testing_out").do(10)


def test_H2():
    # Check all combinations of stances look reasonable
    army_1, army_2, terrain = utils_for_H_tests(Stance.AGG, Stance.BAL)

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
    GraphicBattle(army_1, army_2, landscape, 920, "testing_out").do(10)


def test_H3():
    # Check how DEF behaves on very steep terrain
    army_1, army_2, terrain = utils_for_H_tests(Stance.DEF, Stance.DEF)

    height = {(2.2, 0): -4,
              (0.9, 0): -4,
              (0, 0): -4,
              (-0.9, 0): -4,
              (-2.2, 0): -4,
              (-1.2, 7.5): 5,
              (1.6, 6.5): 0,
              (-1.6, -7.5): 0,
              (1.2, -6.5): 5}
    landscape = Landscape(terrain, height)
    GraphicBattle(army_1, army_2, landscape, 920, "testing_out").do(10)


def test_H4():
    # Check all combinations of stances look reasonable
    army_1, army_2, _ = utils_for_H_tests(Stance.DEF, Stance.DEF)
    army_1.add(0, mixed).add(1, mixed).add(2, mixed)
    army_2.add(-2, mixed).add(-1, mixed).add(0, mixed)

    landscape = PresetLandscapes.rolling_green()  # Landscape(terrain, height)
    GraphicBattle(army_1, army_2, landscape, 920, "testing_out").do(10)
