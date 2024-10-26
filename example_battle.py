from Data import PresetLandscapes, sword, spear, pike, irreg, javelin, archer, mixed, h_horse, l_horse  # noqa
from Globals import Stance
from GraphicBattle import GraphicBattle
from Unit import Army

from Data import spearp, archerm, irregm

army_1 = Army("Blue", Stance.BAL, "DarkBlue")
army_1.add(-2, spearp).add(-1, spear).add(0, spear).add(1, spear).add(2, spearp)

army_2 = Army("Red", Stance.BAL, "DarkRed")
army_2.add(-2, archerm).add(-2, archerm).add(-1, mixed).add(0, mixed).add(1, mixed).add(2, archerm)
army_2.add_reserves(irregm, irregm, irregm)

landscape = PresetLandscapes.sloping()

GraphicBattle(army_1, army_2, landscape, (1080, 720), "example_out").do(10)
