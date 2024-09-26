from Battle import Army, Landscape
from GraphicBattle import GraphicBattle

from Data import flat, even, rough, broken, ragged, \
                 spear, sword, pike, javelin, archer, horse, h_archer, irreg  # noqa


army_1 = Army("1", "DarkBlue").add(-2, horse).add(-1, sword).add(0, sword).add(1, sword).add(2, archer)
army_2 = Army("2", "DarkRed").add(-2, javelin).add(-1, pike).add(0, pike).add(1, pike).add(2, horse)

landscape = Landscape({-2: {-3: even, 1: rough, 3: broken},
                       -1: {-2: rough, 0: even, 2: flat},
                       0: {-2: rough, -1: even, 1: flat},
                       1: {-3: rough, -2: even, 1: flat},
                       2: {-4: even, -3: flat}})

GraphicBattle(army_1, army_2, landscape, (720, 540), "battle_out").do(verbosity=100)
