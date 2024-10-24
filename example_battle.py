from Data import PresetLandscapes, sword, spear, pike, irreg, javelin, archer, h_horse, l_horse  # noqa
from Globals import Stance
from GraphicBattle import GraphicBattle
from Unit import Army

army_1 = Army("Greek", Stance.NEUT, "DarkBlue")
army_1.add(-2, archer).add(-1, pike).add(0, pike).add(1, pike).add(2, archer)

army_2 = Army("Macedon", Stance.AGGR, "DarkRed")
army_2.add(-2, javelin).add(-1, pike).add(0, pike).add(1, h_horse).add(2, spear)

landscape = PresetLandscapes.rolling_green()

GraphicBattle(army_1, army_2, landscape, (1080, 720), "example_out").do(10)
