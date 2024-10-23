from Battle import Army, Stance
from GraphicBattle import GraphicBattle
import Data  # noqa
from Data import PresetLandscapes, \
                 sword, spear, pike, irreg, javelin, archer, h_horse, l_horse  # noqa


army_1 = Army("Rome", Stance.DEFN, "DarkBlue")
army_1.add(-2, archer).add(-1, archer).add(0, spear).add(1, spear).add(2, spear)

army_2 = Army("Macedonia", Stance.DEFN, "DarkRed")
army_2.add(-2, spear).add(-1, spear).add(0, spear).add(1, spear).add(2, spear)

landscape = PresetLandscapes.rocky_hill()

GraphicBattle(army_1, army_2, landscape, (1080, 720), "example_out").do(10)
