from Data import PresetLandscapes, sword, spear, pike, irreg, javelin, archer, mixed, h_horse, l_horse  # noqa
from Globals import Stance
from GraphicBattle import GraphicBattle
from Unit import Army

# from Data import spearp, archerm, irregm, l_horsem

# army_1 = Army("Blue", Stance.BAL, "DarkBlue")
# army_1.add(-2, spearp).add(-1, spear).add(0, spear).add(1, spear).add(2, h_horse)

# army_2 = Army("Red", Stance.BAL, "DarkRed")
# army_2.add(-2, l_horsem).add(-1, archerm).add(-1, mixed).add(0, mixed).add(1, mixed).add(2, archerm)#.add(3, archerm)
# army_2.add_reserves(irregm, irregm, irregm)

# landscape = PresetLandscapes.sloping()
# GraphicBattle(army_1, army_2, landscape, 800, "example_out").do(10)


from Data import line, light, grenadier, cuirassier, hussar, cannon  # noqa

army_1 = Army("Blue", Stance.DEF, "DarkBlue")
army_1.add(-2, light).add(-1, cannon).add(0, line).add(1, line).add(2, hussar)
army_1.add_reserves(grenadier)

army_2 = Army("Red", Stance.BAL, "DarkRed")
army_2.add(-2, line).add(-1, grenadier).add(0, line).add(1, line).add(2, cuirassier)
army_2.add_reserves(hussar)

landscape = PresetLandscapes.sloping()
GraphicBattle(army_1, army_2, landscape, 920, "modern_out2").do(10)
