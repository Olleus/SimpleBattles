from math import inf  # noqa

from Battle import Stance, Army, Landscape
from GraphicBattle import GraphicBattle
import Data
from Data import flat, even, rough, broken, ragged, forest, river, \
                 spear, sword, pike, javelin, archer, horse, h_archer, irreg  # noqa


def preamble():
    return Army("1", Stance.LINE, "DarkBlue"), Army("2", Stance.LINE, "DarkRed")


def do_single_terrain_battle(army_1, army_2, terrain, name="testing_out"):
    files = set(army_1.file_units) | set(army_2.file_units)
    landscape = Landscape({file: {inf: terrain} for file in files})
    GraphicBattle(army_1, army_2, landscape, (1080, 640), name).do(10)


""" spear - sword - pike trichotomy """


def test_1():
    # swords win on even by the faintest of margins, spears win on flat
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, sword).add(1, sword)
    do_single_terrain_battle(army_1, army_2, flat)


def test_2():
    # spears narrowly win on even, ending in a wedge. swords win if rough, ending in a v
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    do_single_terrain_battle(army_1, army_2, rough)


def test_3():
    # pikes push spears off on even, just scrape a win on rough, spears win on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, pike).add(1, pike)
    do_single_terrain_battle(army_1, army_2, rough)


def test_4():
    # pikes confidently win on rough in a wedge. spears win confidently if broken, with a v shape
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-2, pike).add(-1, pike).add(0, pike).add(1, pike).add(2, pike)
    do_single_terrain_battle(army_1, army_2, broken)


def test_5():
    # pikes push swords off on even, swords win on rough
    army_1, army_2 = preamble()
    army_1.add(0, sword).add(1, sword)
    army_2.add(0, pike).add(1, pike)
    do_single_terrain_battle(army_1, army_2, rough)


def test_6():
    # pikes win in a wedge on rough, swords win on broken
    army_1, army_2 = preamble()
    army_1.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    army_2.add(-2, pike).add(-1, pike).add(0, pike).add(1, pike).add(2, pike)
    do_single_terrain_battle(army_1, army_2, rough)


""" Adding in ranged units to the mix """


def test_7():
    # spears push javelins off on rough, but javelins confidently kill them on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, rough)


def test_8():
    # spears push them off on rough, but get killed off on broken
    army_1, army_2 = preamble()
    army_1.add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-1, javelin).add(0, javelin).add(1, javelin).add(2, javelin)
    do_single_terrain_battle(army_1, army_2, broken)


def test_9():
    # sword push javelins off on rough, but javelins just kill them on broken
    army_1, army_2 = preamble()
    army_1.add(0, sword).add(1, sword)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, rough)


def test_10():
    # pikes push off the javelins with minimal damage to anyone on rough, but lose badly on broken
    army_1, army_2 = preamble()
    army_1.add(0, pike).add(1, pike)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, rough)


def test_11():
    # archers win on even (doing better as rougher) and are driven off (with more morale) on flat
    army_1, army_2 = preamble()
    army_1.add(0, javelin).add(1, javelin)
    army_2.add(0, archer).add(1, archer)
    do_single_terrain_battle(army_1, army_2, even)


def test_12():
    # spear pushes off archers when there are 3 files, but die when there are just two
    army_1, army_2 = preamble()
    army_1.add(-1, spear).add(0, spear).add(1, spear)
    army_2.add(-1, archer).add(0, archer).add(1, archer)
    do_single_terrain_battle(army_1, army_2, rough)


""" Adding in cavalry units to the mix """


def test_13():
    # spear narrowly on even, horse pushes spears off on flat
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, horse).add(1, horse)
    do_single_terrain_battle(army_1, army_2, flat)


def test_14():
    # horse-army wins on even, loses on forest
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(1, horse).add(2, horse)
    do_single_terrain_battle(army_1, army_2, even)


def test_15():
    # horse archers win when 1v1, get pushed back on all terrain in 2v2
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, h_archer).add(1, h_archer)
    do_single_terrain_battle(army_1, army_2, broken)


def test_16():
    # h_archers pushed back on rough, win on broken
    army_1, army_2 = preamble()
    army_1.add(0, horse).add(1, horse)
    army_2.add(0, h_archer).add(1, h_archer)
    do_single_terrain_battle(army_1, army_2, rough)


""" Checking reserves work as intended """


def test_17():
    # Reserves come in at the correct time and all is displayed as expected
    army_1, army_2 = preamble()
    army_1.add(0, pike).add_reserves(pike, pike, pike, pike, pike, pike)
    army_2.add(0, sword).add_reserves(sword, sword, sword, sword, sword, sword)
    do_single_terrain_battle(army_1, army_2, ragged)


def test_18():
    # Side with reserves wins (in a very artificial scenario)
    army_1, army_2 = preamble()
    army_1.add(-1, sword).add(0, sword).add_reserves(horse)
    army_2.add(-1, sword).add(0, sword).add(1, horse)

    landscape = Landscape({-1: {inf: flat},
                           0: {inf: flat},
                           1: {inf: river}})

    GraphicBattle(army_1, army_2, landscape, (720, 480), "testing_out").do(verbosity=10)


def test_19():
    # Loss for army 1 when all deployed, but a win if javelins are pulled into reserves
    army_1, army_2 = preamble()
    army_1.add(-1, horse).add(0, sword).add(1, sword).add(2, javelin)
    army_2.add(-1, horse).add(0, spear).add(1, spear).add(2, horse)

    landscape = Landscape({-1: {1: broken, inf: rough},
                           0: {-1: rough, 2: even, inf: flat},
                           1: {1: rough, inf: even},
                           2: {-4: broken, -1: rough, 2: even, inf: flat}})

    GraphicBattle(army_1, army_2, landscape, (720, 480), "testing_out").do(verbosity=10)


def test_20():
    # 3+2 loses to 5+0 when deployed in the centre, but wins when deployed at the edge
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-1, spear).add(0, spear).add(1, spear).add_reserves(spear, spear)
    do_single_terrain_battle(army_1, army_2, even)


def test_21():
    # 4+1 beat 5+0 and 3+2 (no matter where it's deployed)
    # Does not hold for small armies: 2+1 loses to 3+0
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add_reserves(spear)
    landscape = Data.landscape_river()

    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(verbosity=10)


""" Testing how many weak units are needed to defeat a strong one """


def test_22():
    # Spears only just victorious with an 135 power advantage

    from Battle import UnitType
    militia = UnitType("Militia", 165)

    army_1, army_2 = preamble()
    army_1.add(0, spear)
    army_2.add(-1, militia).add(0, militia).add(1, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_23():
    # Spears only just victorious with an 80 power advantage
    from Battle import UnitType
    militia = UnitType("Militia", 220)

    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    do_single_terrain_battle(army_1, army_2, even)


def test_24():
    # Spears only just victorious with an 100 power advantage
    from Battle import UnitType
    militia = UnitType("Militia", 200)

    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(-1, militia).add(0, militia).add(1, militia).add(2, militia)
    army_2.add_reserves(militia)
    do_single_terrain_battle(army_1, army_2, even)


""" Testing height """


def test_25():
    # Minimum heigh difference for sword to beat pike
    army_1, army_2 = preamble()
    army_1.add(0, sword)
    army_2.add(0, pike)
    terrain = {0: {inf: flat}}
    height = {(0, -2): 2.95, (0, 2): 0}
    landscape = Landscape(terrain, height)
    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(10)


def test_26():
    # Army_1 wins with height map, loses if it's removed
    # Also check that contours are drawn properly
    army_1, army_2 = preamble()

    army_1.add(-2, archer).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    army_1.add_reserves(horse)
    army_2.add(-2, javelin).add(-1, spear).add(0, pike).add(1, pike).add(2, pike)
    army_2.add_reserves(javelin)

    terrain = {-3: {-1: broken, 3: rough, inf: even},
               -2: {-1: broken, 2: rough, inf: rough},
               -1: {0: rough, inf: even},
               0: {-2: rough, 2: even, inf: flat},
               1: {0: rough, 3: even, inf: flat},
               2: {1: even, inf: flat},
               3: {-3: even, inf: flat}}
    height = {(-0.5, -3): 5,
              (0.5, -3): 4,
              (-1.75, 2): 0,
              (0, 3): 1,
              (1.75, 2): 1}
    landscape = Landscape(terrain, height)

    GraphicBattle(army_1, army_2, landscape, (1080, 720), "testing_out").do(verbosity=10)


test_20()
