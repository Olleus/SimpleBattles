from Battle import Stance, Army
from GraphicBattle import GraphicBattle
from Data import flat, even, rough, broken, ragged, forest, river, PresetLandscapes, \
                 spear, sword, pike, javelin, archer, horse, h_archer, irreg  # noqa


army_1 = Army("Rome", Stance.HOLD, "DarkBlue")
army_1.add(-2, sword).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
army_1.add_reserves(horse)

army_2 = Army("Macedonia", Stance.LINE, "DarkRed")
army_2.add(-2, javelin).add(-1, pike).add(0, pike).add(1, pike).add(2, pike)
army_2.add_reserves(horse)

landscape = PresetLandscapes.ridge()

GraphicBattle(army_1, army_2, landscape, (1080, 720), "example_out").do(10)
