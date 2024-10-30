from Data import PresetLandscapes, sword, spear, pike, irreg, javelin, archer, mixed, h_horse, l_horse  # noqa
from Globals import Stance
from GraphicBattle import GraphicBattle
from Unit import Army


# army_1 = Army("Blue", Stance.DEF, "DarkBlue")
# army_1.add(-2, h_horse).add(-1, spear).add(0, spear).add(1, spear).add(2, l_horse)
# army_1.add_reserves(spear)

# army_2 = Army("Red", Stance.BAL, "DarkRed")
# army_2.add(-2, archer).add(-1, mixed).add(0, mixed).add(1, pike).add(2, pike)  # .add(3, h_horse)
# army_2.add_reserves(sword)

# landscape = PresetLandscapes.valley()
# GraphicBattle(army_1, army_2, landscape, 800, "example_out").do(10)


from Data import line, light, grenadier, cuirassier, hussar, cannon  # noqa

army_1 = Army("Blue", Stance.DEF, "DarkBlue")
army_1.add(-2, light).add(-1, cannon).add(0, line).add(1, line).add(2, hussar)
army_1.add_reserves(grenadier)

army_2 = Army("Red", Stance.BAL, "DarkRed")
army_2.add(-3, hussar).add(-1, grenadier).add(0, line).add(1, line).add(2, line)
army_2.add_reserves(cuirassier)

landscape = PresetLandscapes.sloping()
GraphicBattle(army_1, army_2, landscape, 800, "modern_out").do(10)
