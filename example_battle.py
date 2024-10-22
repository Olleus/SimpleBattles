from Battle import Army, Stance
from GraphicBattle import GraphicBattle
import Data  # noqa
from Data import PresetLandscapes, \
                 sword, spear, pike, irreg, javelin, archer, h_horse, l_horse  # noqa


army_1 = Army("Rome", Stance.LINE, "DarkBlue")
army_1.add(-3, irreg).add(-2, l_horse).add(-1, sword).add(0, sword).add(1, sword).add(2, sword)
army_1.add_reserves(h_horse)

army_2 = Army("Macedonia", Stance.LINE, "DarkRed")
army_2.add(-2, spear).add(-1, pike).add(0, pike).add(1, spear).add(2, h_horse).add(3, l_horse)
army_2.add_reserves(spear)

landscape = PresetLandscapes.rolling_green()

GraphicBattle(army_1, army_2, landscape, (900, 720), "example_out").do(10)
