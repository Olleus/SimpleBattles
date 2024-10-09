from math import inf

from Battle import BASE_SPEED, Landscape, Terrain, UnitType


#######################
"""    UNIT TYPE    """
#######################

spear = UnitType("Spear", 300)
sword = UnitType("Sword", 290, -0.25)
pike = UnitType("Pike", 325, 0.6)

irreg = UnitType("Irregular", 270, -0.4, speed=1.25*BASE_SPEED, att_range=1.2)
javelin = UnitType("Javelin", 250, -0.6, att_range=2)
archer = UnitType("Archer", 230, -0.5, att_range=5)

horse = UnitType("Horse", 280, -0.4, speed=2*BASE_SPEED)
h_archer = UnitType("H. Archer", 245, -0.7, speed=2*BASE_SPEED, att_range=3)


#####################
"""    TERRAIN    """
#####################

flat = Terrain("Flat", "LawnGreen", roughness=-0.15)
even = Terrain("Even", "GreenYellow", roughness=0)
rough = Terrain("Rough", "YellowGreen", roughness=0.1)
broken = Terrain("Broken", "Khaki", roughness=0.2)
ragged = Terrain("Ragged", "BurlyWood", roughness=0.3)

forest = Terrain("Forest", "ForestGreen", roughness=0.6, cover=0.5, penalty=True)
river = Terrain("River", "DodgerBlue", roughness=0.8, cover=-0.5, penalty=True)


class PresetLandscapes:
    """Static container of pre-defined landscapes"""

    @staticmethod
    def flat() -> Landscape:
        terrain = {file: {inf: flat} for file in range(-2, 3)}
        return Landscape(terrain, {})

    @staticmethod
    def even() -> Landscape:
        terrain = {file: {inf: even} for file in range(-2, 3)}
        return Landscape(terrain, {})

    @staticmethod
    def rough() -> Landscape:
        terrain = {file: {inf: rough} for file in range(-2, 3)}
        return Landscape(terrain, {})

    @staticmethod
    def broken() -> Landscape:
        terrain = {file: {inf: broken} for file in range(-2, 3)}
        return Landscape(terrain, {})

    @staticmethod
    def ragged() -> Landscape:
        terrain = {file: {inf: ragged} for file in range(-2, 3)}
        return Landscape(terrain, {})

    @staticmethod
    def forest() -> Landscape:
        terrain = {file: {inf: forest} for file in range(-2, 3)}
        return Landscape(terrain, {})

    @staticmethod
    def hill() -> Landscape:
        terrain = {-2: {inf: even},
                   -1: {-2: even, 2: forest, inf: even},
                   0: {-3: even, -1: forest, 1: ragged, 3: forest, inf: even},
                   1: {-2: even, 2: forest, inf: even},
                   2: {inf: even}}

        height: dict[tuple[float, float], float] = {(0, 0): 5,
                                                    (-0.6, 0.5): 4,
                                                    (0.6, -0.5): 4,
                                                    (-3, -10): 0,
                                                    (-3, 10): 0,
                                                    (3, -10): 0,
                                                    (3, 10): 0}
        
        return Landscape(terrain, height)

    @staticmethod
    def river() -> Landscape:
        terrain = {file: {-2: even, -0.5: broken, 0.5: river, 2: broken, inf: even}
                   for file in range(-2, 3)}

        height: dict[tuple[float, float], float] = {(0, 0): -2,
                                                    (-1.2, 0): -3,
                                                    (1.2, 0): -2,
                                                    (-2.3, 0): -3,
                                                    (2.3, 0): -2,
                                                    (-1.4, -5): 0,
                                                    (-1.5, 5): 0,
                                                    (1.6, -5): 0,
                                                    (1.5, 5): 0}
        
        return Landscape(terrain, height)

    @staticmethod
    def ridge() -> Landscape:
        terrain = {-2: {-1: broken, 2: rough, inf: rough},
                   -1: {0: rough, inf: even},
                   0: {-2: rough, 2: even, inf: flat},
                   1: {0: rough, 3: even, inf: flat},
                   2: {1: even, inf: flat}}

        height: dict[tuple[float, float], float] = {(-0.4, -3.0): 5,
                                                    (0.4, -3): 4,
                                                    (-1.75, 2): 0,
                                                    (0, 3): 1,
                                                    (1.75, 2): 1}
        
        return Landscape(terrain, height)


# Collections for easy referencing, especially to build interfact in pyscript

unit_dict = {x.name: x for x in globals().values() if isinstance(x, UnitType)}
landscape_dict = {k: v for k, v in PresetLandscapes.__dict__.items()
                  if isinstance(v, staticmethod) and v.__annotations__["return"] is Landscape}
