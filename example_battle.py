from math import inf

from Battle import Army, Landscape
from GraphicBattle import GraphicBattle
from Data import flat, even, rough, broken, ragged, forest, river, \
                 spear, sword, pike, javelin, archer, horse, h_archer, irreg  # noqa


army_1 = Army("A", "DarkBlue")
army_1.add(-2, horse).add(-1, sword).add(0, sword).add(1, sword).add(3, javelin)
army_1.add_reserves(sword, horse)

army_2 = Army("B", "DarkRed")
army_2.add(-2, archer).add(-1, spear).add(0, pike).add(1, pike).add(2, horse)
army_2.add_reserves(spear, spear)


landscape = Landscape({-2: {-3: even, 1: rough, 3: broken, inf: even},
                       -1: {-2: rough, 0: even, inf: flat},
                       0: {-2: rough, -1: even, inf: flat},
                       1: {-3: rough, -2: even, inf: flat},
                       2: {-4: even, 1: flat, inf: even}})

landscpe2 = Landscape({-2: {-3: flat, -1.2: even, -0.5: river, 1.5: even, inf: forest},
                       -1: {-3: even, -1: rough, 0: river, 2: even, inf: forest},
                       0: {-4: even, -0.95: rough, 0.3: river, 2.5: even, inf: forest},
                       1: {-4: even, -1: rough, 0.2: river, 2: even, inf: forest},
                       2: {-5: even, -2: rough, -0.8: broken, 0.1: river, 1.5: rough, inf: forest}})


GraphicBattle(army_1, army_2, landscape, (1280, 800), "example_out").do(verbosity=10)
