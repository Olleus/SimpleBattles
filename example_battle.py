from math import inf

from Battle import Army, Landscape
from GraphicBattle import GraphicBattle
from Data import flat, even, rough, broken, ragged, forest, river, \
                 spear, sword, pike, javelin, archer, horse, h_archer, irreg  # noqa


army_1 = Army("Rome", "DarkBlue")
army_2 = Army("Macedonia", "DarkRed")

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

height = {(-0.5, -3.0): 5.0,
          (0.5, -3): 4,
          (-1.75, 2): 0,
          (0, 3): 1,
          (1.75, 2): 1}

landscape = Landscape(terrain, height)

GraphicBattle(army_1, army_2, landscape, (1080, 720), "example_hill").do(verbosity=10)
