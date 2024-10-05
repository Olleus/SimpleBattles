from Battle import BASE_SPEED, Terrain, UnitType

"""    TERRAIN    """

flat = Terrain("Flat", "LawnGreen", roughness=-0.15)
even = Terrain("Even", "GreenYellow", roughness=0)
rough = Terrain("Rough", "YellowGreen", roughness=0.1)
broken = Terrain("Broken", "Khaki", roughness=0.2)
ragged = Terrain("Ragged", "BurlyWood", roughness=0.3)

forest = Terrain("Forest", "ForestGreen", roughness=0.6, cover=0.5)
river = Terrain("River", "DodgerBlue", roughness=0.8, cover=-0.5, penalty=True)

"""    UNIT TYPE    """

spear = UnitType("Spear", 300)
sword = UnitType("Legion", 290, -0.25)
pike = UnitType("Pike", 325, 0.6)

javelin = UnitType("Javelin", 250, -0.6, att_range=2)
archer = UnitType("Archer", 230, -0.5, att_range=5)

horse = UnitType("Horse", 280, -0.4, speed=2*BASE_SPEED)
h_archer = UnitType("H. Archer", 245, -0.7, speed=2*BASE_SPEED, att_range=3)

irreg = UnitType("Irregular", 270, -0.4, speed=1.25*BASE_SPEED, att_range=1.2)
