from Battle import Army, Stance
from GraphicBattle import GraphicBattle
from Data import PresetLandscapes, \
                 sword, spear, pike, irreg, javelin, archer, h_horse, l_horse  # noqa


army_1 = Army("Rome", Stance.LINE, "DarkBlue")
army_1.add(-2, archer).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
army_1.add_reserves(h_horse)

army_2 = Army("Macedonia", Stance.LINE, "DarkRed")
army_2.add(-2, javelin).add(-1, pike).add(0, pike).add(1, pike).add(2, pike)
army_2.add_reserves(l_horse)

landscape = PresetLandscapes.ridge()

GraphicBattle(army_1, army_2, landscape, (1080, 720), "example_out").do(10)
