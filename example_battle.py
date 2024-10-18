from Battle import Army, Stance
from GraphicBattle import GraphicBattle
import Data
from Data import PresetLandscapes, \
                 sword, spear, pike, irreg, javelin, archer, h_horse, l_horse  # noqa


army_1 = Army("Rome", Stance.FAST, "DarkBlue")
army_1.add(-2, Data.l_horse).add(-1, pike)
army_1.add_reserves(pike, pike, pike)

army_2 = Army("Macedonia", Stance.LINE, "DarkRed")
army_2.add(2, Data.pike)
army_2.add_reserves(pike, pike, pike, pike, pike)

landscape = PresetLandscapes.forest()

GraphicBattle(army_1, army_2, landscape, (900, 720), "example_out").do(10)
