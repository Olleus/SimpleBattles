from Battle import Army, Landscape
from GraphicBattle import GraphicBattle

from Data import flat, even, rough, broken, ragged, \
                 spear, sword, pike, javelin, archer, horse, h_archer, irreg  # noqa


def preamble():
    return Army("1", "DarkBlue"), Army("2", "DarkRed")


def do_single_terrain_battle(army_1, army_2, terrain, name="battle_out"):
    files = set(army_1.file_units) | set(army_2.file_units)
    landscape = Landscape({file: {0: terrain} for file in files})
    GraphicBattle(army_1, army_2, landscape, (720, 240), name).do(1)


""" spear - sword - pike trichotomy """


def test_1():
    # swords win on even by the faintest of margins, spears win on flat
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, sword).add(1, sword)
    do_single_terrain_battle(army_1, army_2, even, "spear-sword-even-2")


def test_2():
    # spears narrowly win on even, ending in a wedge. swords win if rough, ending in a v
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
    do_single_terrain_battle(army_1, army_2, even, "spear-sword-even-5")


def test_3():
    # pikes push spears off on even, just scrape a win on rough, spears win on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, pike).add(1, pike)
    do_single_terrain_battle(army_1, army_2, broken)


def test_4():
    # pikes confidently win on rough in a wedge. spears win confidently if broken, with a v shape
    army_1, army_2 = preamble()
    army_1.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-2, pike).add(-1, pike).add(0, pike).add(1, pike).add(2, pike)
    do_single_terrain_battle(army_1, army_2, rough)


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
    do_single_terrain_battle(army_1, army_2, broken, "pike-sword-broken-5")


""" Adding in ranged units to the mix """


def test_7():
    # spears push javelins off on rough, but javelins confidently kill them on broken
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, broken)


def test_8():
    # spears push them off on broken, but get killed off on ragged
    army_1, army_2 = preamble()
    army_1.add(-1, spear).add(0, spear).add(1, spear).add(2, spear)
    army_2.add(-1, javelin).add(0, javelin).add(1, javelin).add(2, javelin)
    do_single_terrain_battle(army_1, army_2, ragged)


def test_9():
    # sword push javelins off on broken, but javelins kill them on ragged
    army_1, army_2 = preamble()
    army_1.add(0, sword).add(1, sword)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, broken)


def test_10():
    # pikes push off the javelins with minimal damage to anyone on rough, but lose badly on broken
    army_1, army_2 = preamble()
    army_1.add(0, pike).add(1, pike)
    army_2.add(0, javelin).add(1, javelin)
    do_single_terrain_battle(army_1, army_2, broken)


def test_11():
    # archers win on even (doing better as rougher) and are driven off (with more morale) on flat
    army_1, army_2 = preamble()
    army_1.add(0, javelin).add(1, javelin)
    army_2.add(0, archer).add(1, archer)
    do_single_terrain_battle(army_1, army_2, flat)


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
    # horse-army wins on flat & even, draw on the rough ones
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(1, spear).add(2, horse)
    do_single_terrain_battle(army_1, army_2, rough)


def test_15():
    # horse archers win on all terrain when 1v1, get pushed back on all terrain in 2v2
    army_1, army_2 = preamble()
    army_1.add(0, spear).add(1, spear)
    army_2.add(0, h_archer).add(1, h_archer)
    do_single_terrain_battle(army_1, army_2, rough)


def test_16():
    # h_archers pushed back on broken, win on ragged
    army_1, army_2 = preamble()
    army_1.add(0, horse).add(1, horse)
    army_2.add(0, h_archer).add(1, h_archer)
    do_single_terrain_battle(army_1, army_2, ragged)


def main():
    army_1, army_2 = preamble()
    army_1.add(-2, horse).add(-1, sword).add(0, sword).add(1, sword).add(2, archer)
    army_2.add(-2, javelin).add(-1, pike).add(0, pike).add(1, pike).add(2, horse)

    landscape = Landscape({-2: {-3: even, 1: rough, 3: broken},
                           -1: {-2: rough, 0: even, 2: flat},
                           0: {-2: rough, -1: even, 1: flat},
                           1: {-3: rough, -2: even, 1: flat},
                           2: {-4: even, -3: flat}})
    GraphicBattle(army_1, army_2, landscape, (720, 540), "battle_out").do(1)


main()
