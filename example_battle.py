from Data import PresetLandscapes, sword, spear, pike, irreg, javelin, archer, mixed, h_horse, l_horse  # noqa
from Globals import Stance
from GraphicBattle import GraphicBattle
from Unit import Army

army_1 = Army("Greek", Stance.BAL, "DarkBlue")
army_1.add(-2, archer).add(-1, archer).add(0, spear).add(1, spear).add(2, h_horse).add(3, h_horse)

army_2 = Army("Persia", Stance.DEF, "DarkRed")
army_2.add(-2, h_horse).add(-1, mixed).add(0, mixed).add(1, mixed).add(2, javelin).add(-3, l_horse)

landscape = PresetLandscapes.rolling_green()

GraphicBattle(army_1, army_2, landscape, (1080, 720), "example_out").do(10)
