from Battle import Army, Stance
from GraphicBattle import GraphicBattle
import Data
from Data import PresetLandscapes, \
                 sword, spear, pike, irreg, javelin, archer, h_horse, l_horse  # noqa


army_1 = Army("Rome", Stance.FAST, "DarkBlue")
army_1.add(-1, Data.irregp).add(0, Data.swordp).add(1, Data.swordp).add(2, Data.swordp)
# army_1.add_reserves(h_horse)

army_2 = Army("Macedonia", Stance.LINE, "DarkRed")
army_2.add(-1, javelin).add(0, pike).add(1, pike).add(2, Data.l_horsem)
army_2.add_reserves(l_horse)

landscape = PresetLandscapes.river_side()

GraphicBattle(army_1, army_2, landscape, (900, 720), "example_out").do(10)
