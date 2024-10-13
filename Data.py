from math import inf

from Battle import Landscape, Terrain, UnitType


#######################
"""    UNIT TYPE    """
#######################

# Melee
swordm = UnitType("Sword-", 240, 0)
sword = UnitType("Sword", 290, 0)
swordp = UnitType("Sword+", 340, 0)

spearm = UnitType("Spear-", 250, 0.2)
spear = UnitType("Spear", 300, 0.2)
spearp = UnitType("Spear+", 350, 0.2)

pikem = UnitType("Pike-", 270, 0.6)
pike = UnitType("Pike", 320, 0.6)
pikep = UnitType("Pike+", 370, 0.6)

# Ranged
irregm = UnitType("Irregular-", 210, -0.3, speed=1.1, att_range=1.3)
irreg = UnitType("Irregular", 260, -0.3, speed=1.1, att_range=1.3)    # smoothness_desire = -0.2
irregp = UnitType("Irregular+", 310, -0.3, speed=1.1, att_range=1.3)

javelinm = UnitType("Javelin-", 190, -0.5, speed=1.2, att_range=2)
javelin = UnitType("Javelin", 240, -0.5, speed=1.2, att_range=2)      # smoothness_desire = -0.3
javelinp = UnitType("Javelin+", 290, -0.5, speed=1.2, att_range=2)

archerm = UnitType("Archer-", 170, -0.3, att_range=5)
archer = UnitType("Archer", 220, -0.3, att_range=5)
archerp = UnitType("Archer+", 270, -0.3, att_range=5)

# Cavalry
h_horsem = UnitType("Shock Cav-", 240, -0.2, speed=2)
h_horse = UnitType("Shock Cav", 290, -0.2, speed=2)                   # smoothness_desire = 0.8
h_horsep = UnitType("Shock Cav+", 340, -0.2, speed=2)

l_horsem = UnitType("Light Cav-", 185, -0.6, speed=2.3, att_range=3)
l_horse = UnitType("Light Cav", 235, -0.6, speed=2.3, att_range=3)    # smoothness_desire = 0.7
l_horsep = UnitType("Light Cav+", 285, -0.6, speed=2.3, att_range=3)


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
    def forested_hill() -> Landscape:
        terrain = {
            -3: {inf: even},
            -2: {-1.5: even, 3: rough, inf: even},
            -1: {-2.5: even, 4.5: forest, inf: even},
            0: {-5: even, -3.5: rough, 3.5: forest, 5: rough, inf: even},
            1: {-4.5: even, 2.5: forest, inf: even},
            2: {-3: even, 1.5: rough, inf: even},
            3: {inf: even}}

        height: dict[tuple[float, float], float] = {(0, 0): 5,
                                                    (-0.9, -5.1): 0,
                                                    (-1.1, 5.2): 0,
                                                    (1, -5.2): 0,
                                                    (1.1, 4.9): 0}
        return Landscape(terrain, height)

    @staticmethod
    def rocky_hill() -> Landscape:
        terrain = {
            -3: {inf: even},
            -2: {-3: even, 1.5: broken, inf: even},
            -1: {-3: even, -1.5: broken, 1: ragged, 2: broken, inf: even},
            0: {-4: even, -3: broken, 3: ragged, 4: broken, inf: even},
            1: {-2: even, -1: broken, 1.5: ragged, 3: broken, inf: even},
            2: {-1.5: even, 3: broken, inf: even},
            3: {inf: even}}

        height: dict[tuple[float, float], float] = {(0, 0): 6,
                                                    (-0.5, -5.1): 0,
                                                    (-0.7, 5.2): 0,
                                                    (0.6, -5.2): 0,
                                                    (0.7, 4.9): 0,
                                                    (-3, 0): 0,
                                                    (3, 0): 0}
        return Landscape(terrain, height)

    @staticmethod
    def ridge() -> Landscape:
        terrain = {-3: {-2: ragged, 3: broken, inf: rough},
                   -2: {-0.5: broken, 4: rough, inf: even},
                   -1: {1: rough, inf: even},
                   0: {-2: rough, 2: even, inf: smooth},
                   1: {0: rough, 3: even, inf: smooth},
                   2: {1: even, inf: smooth},
                   3: {-2: even, inf: smooth}}

        height: dict[tuple[float, float], float] = {(-1.9, -4.5): 5,
                                                    (-0.4, -4): 5,
                                                    (1, -4): 4,
                                                    (0, 4): 0,
                                                    (-0.8, 1.5): 0,
                                                    (1.7, 2): 0,
                                                    (-2.2, 2.5): 0}
        return Landscape(terrain, height)

    @staticmethod
    def valley() -> Landscape:
        terrain = {-3: {-2: rough, 2: forest, inf: rough},
                   -2: {-3: rough, 3: even, inf: rough},
                   -1: {-3: rough, -1.5: even, 1.5: smooth, 4: even, inf: rough},
                   0: {-4: rough, -2: even, 2: smooth, 4: even, inf: rough},
                   1: {-4: rough, -2.5: even, 2: smooth, 4: even, inf: rough},
                   2: {-4.5: rough, -3: even, 2.5: smooth, 4.5: even, inf: rough},
                   3: {-3: even, 3: smooth, inf: even}}

        height: dict[tuple[float, float], float] = {(2.8, 0): 0,
                                                    (1.4, 0): 0,        
                                                    (0, 0): 0,
                                                    (-1.4, 0): 0,
                                                    (-2.8, 0): 0,
                                                    (-1.4, 4.8): 4,
                                                    (1.8, 5.2): 3,
                                                    (-1.8, -4.8): 3,
                                                    (1.4, -5.2): 4,
                                                    (0, -7): 5,
                                                    (0, 7): 5}
        return Landscape(terrain, height)

    @staticmethod
    def river_side() -> Landscape:
        terrain = {-3: {inf: ragged},
                   -2: {inf: broken},
                   -1: {inf: even},
                   0: {inf: even},
                   1: {inf: smooth},
                   2: {inf: smooth},
                   3: {inf: river}}

        height: dict[tuple[float, float], float] = {(-3, 4): 5,
                                                    (-3, -4): 5,
                                                    (-1.4, -6): 3,
                                                    (-1.2, 0): 3,
                                                    (-1.4, 6): 3,
                                                    (2.4, -4.8): -1,
                                                    (2.6, 0): -1,
                                                    (2.4, 4.8): -1}
        return Landscape(terrain, height)

    @staticmethod
    def river_crossing() -> Landscape:
        terrain = {file: {-4: even, -2: rough, -0.75: broken, 0.75: river,
                          2: broken, 4: rough, inf: even}
                   for file in range(-4, 5)}

        height: dict[tuple[float, float], float] = {(2.8, 0): -3,
                                                    (1.2, 0): -3,
                                                    (0, 0): -3,
                                                    (-1.2, 0): -3,
                                                    (-2.8, 0): -3,
                                                    (-1.2, 7.8): 3,
                                                    (1.6, 6.2): 1,
                                                    (-1.6, -7.8): 1,
                                                    (1.2, -6.2): 3}
        return Landscape(terrain, height)

    @staticmethod
    def smooth() -> Landscape:
        terrain = {file: {inf: smooth} for file in range(-4, 5)}
        return Landscape(terrain, {})

    @staticmethod
    def even() -> Landscape:
        terrain = {file: {inf: even} for file in range(-4, 5)}
        return Landscape(terrain, {})

    @staticmethod
    def rough() -> Landscape:
        terrain = {file: {inf: rough} for file in range(-4, 5)}
        return Landscape(terrain, {})

    @staticmethod
    def broken() -> Landscape:
        terrain = {file: {inf: broken} for file in range(-4, 5)}
        return Landscape(terrain, {})

    @staticmethod
    def ragged() -> Landscape:
        terrain = {file: {inf: ragged} for file in range(-4, 5)}
        return Landscape(terrain, {})

    @staticmethod
    def forest() -> Landscape:
        terrain = {file: {inf: forest} for file in range(-4, 5)}
        return Landscape(terrain, {})


# Collections for easy referencing, especially to build interfact in pyscript

unit_dict = {x.name: x for x in globals().values() if isinstance(x, UnitType)}
terrain_dict = {x.name: x for x in globals().values() if isinstance(x, Terrain)}
landscape_dict = {k: v for k, v in PresetLandscapes.__dict__.items()
                  if isinstance(v, staticmethod) and v.__annotations__["return"] is Landscape}
