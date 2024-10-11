from math import inf

from Battle import Landscape, Terrain, UnitType


#######################
"""    UNIT TYPE    """
#######################

sword = UnitType("Sword", 290, 0)
spear = UnitType("Spear", 300, 0.2)
pike = UnitType("Pike", 320, 0.6)

irreg = UnitType("Irregular", 270, -0.3, speed=1.1, att_range=1.3)  # eff_ter_rgd = -0.2
javelin = UnitType("Javelin", 250, -0.5, speed=1.2, att_range=2)    # eff_ter_rgd = -0.3
archer = UnitType("Archer", 235, -0.3, att_range=5)

h_horse = UnitType("Heavy Cav", 290, -0.2, speed=2)                 # eff_ter_rgd = 0.8
l_horse = UnitType("Light Cav", 245, -0.6, speed=2.3, att_range=3)  # eff_ter_rgd = 0.7


#####################
"""    TERRAIN    """
#####################

smooth = Terrain("Smooth", "LawnGreen", roughness=-0.2)
even = Terrain("Even", "GreenYellow", roughness=0)
rough = Terrain("Rough", "YellowGreen", roughness=0.1)
broken = Terrain("Broken", "Khaki", roughness=0.2)
ragged = Terrain("Ragged", "BurlyWood", roughness=0.3)

forest = Terrain("Forest", "OliveDrab", roughness=0.4, cover=0.5, penalty=True)
river = Terrain("River", "DodgerBlue", roughness=0.5, cover=-0.5, penalty=True)


class PresetLandscapes:
    """Static container of pre-defined landscapes"""

    @staticmethod
    def smooth() -> Landscape:
        terrain = {file: {inf: smooth} for file in range(-2, 3)}
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
        terrain = {file: {-4: even, -2: rough, -0.75: broken, 0.75: river,
                          2: broken, 4: rough, inf: even}
                   for file in range(-2, 3)}

        height: dict[tuple[float, float], float] = {(2.2, 0): -3,
                                                    (0.9, 0): -3,
                                                    (0, 0): -3,
                                                    (-0.9, 0): -3,
                                                    (-2.2, 0): -3,
                                                    (-1.2, 7.8): 3,
                                                    (1.6, 6.2): 0,
                                                    (-1.6, -7.8): 0,
                                                    (1.2, -6.2): 3}
        
        return Landscape(terrain, height)

    @staticmethod
    def ridge() -> Landscape:

        terrain = {-2: {-1: broken, 2: rough, inf: rough},
                   -1: {0: rough, inf: even},
                   0: {-2: rough, 2: even, inf: smooth},
                   1: {0: rough, 3: even, inf: smooth},
                   2: {1: even, inf: smooth}}

        height: dict[tuple[float, float], float] = {(-0.4, -4): 5,
                                                    (1, -4): 3,
                                                    (0, 4): 0,
                                                    (-1.1, 1.5): -1,
                                                    (1.3, 2): -1}

        return Landscape(terrain, height)


# Collections for easy referencing, especially to build interfact in pyscript

unit_dict = {x.name: x for x in globals().values() if isinstance(x, UnitType)}
terrain_dict = {x.name: x for x in globals().values() if isinstance(x, Terrain)}
landscape_dict = {k: v for k, v in PresetLandscapes.__dict__.items()
                  if isinstance(v, staticmethod) and v.__annotations__["return"] is Landscape}
