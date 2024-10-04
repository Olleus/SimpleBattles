from math import inf

from Battle import Army, Landscape
from GraphicBattle import GraphicBattle
from Data import flat, even, rough, broken, ragged, forest, river, \
                 spear, sword, pike, javelin, archer, horse, h_archer, irreg  # noqa


army_1 = Army("A", "DarkBlue")
army_2 = Army("B", "DarkRed")

army_1.add(2, horse).add(1, sword).add(0, sword).add(-1, sword).add(-2, javelin)
army_2.add(1, horse).add(0, spear).add(-1, spear).add(-2, horse).add(-3, horse)

landscape = Landscape({-3: {-1: rough, inf: even},
                       -2: {0: rough, inf: even},
                       -1: {1: broken, inf: rough},
                       0: {-2: rough, 2: even, inf: flat},
                       1: {0: rough, inf: even},
                       2: {-1: even, inf: flat},
                       3: {-3: even, inf: flat}})

GraphicBattle(army_1, army_2, landscape, (1280, 800), "example_out").do(verbosity=10)
