"""Contains all elements related to terrain, landscapes, and maps the battle takes place on"""

from attrs import define, Factory, field, validators

from Globals import FILE_WIDTH


@define(frozen=False)
class Terrain:
    """The different sorts of terrain that a landscape can be composed of"""
    name: str
    color: str = field(default="White")  # Must match HTML color names
    roughness: float = field(default=0, validator=[validators.gt(-1), validators.lt(1)])
    cover: float = field(default=0, validator=[validators.gt(-1), validators.lt(1)])
    penalty: bool = field(default=False)  # If true, roughness only decreases power


DEFAULT_TERRAIN = Terrain("Undefined", "White")


@define
class Landscape:
    """The map battles take place on, composed of terrains 'tiles' and an interpolatd height map"""
    # VALIDATOR
    def is_inner_dict_sorted(self, attribute, value):
        for inner in value.values():
            keys = list(inner.keys())
            if not keys == sorted(keys):
                raise ValueError("Keys in inner dict are not sorted as expected")

    MAX_HEIGHT_INTERPOL = 10  # Number of points used to interpolate height

    # Outer key is file, inner key upper limit to which that terrain goes to (from prior one)
    terrain_map: dict[int, dict[float, Terrain]] = field(
        converter=lambda x: dict(sorted(x.items())), validator=is_inner_dict_sorted)

    # {(file, pos): height} - height at other locations interpolated from these
    height_map: dict[tuple[float, float], float] = field(default=Factory(dict))

    def get_terrain(self, file: int, pos: float) -> Terrain:
        file_map = self.terrain_map.get(file, {})
        for pos_bound, terrain in file_map.items():
            if pos < pos_bound:
                return terrain
        return DEFAULT_TERRAIN

    def get_mean_cover(self, file: int, pos: float) -> float:
        file_map = self.terrain_map.get(file, {})
        min_pos, max_pos = pos-0.5, pos+0.5
        cover = 0.0

        for pos_bound, terrain in file_map.items():
            if max_pos <= pos_bound:
                cover += terrain.cover * (max_pos - min_pos)  # Remaining interval width
                break
            elif min_pos <= pos_bound:
                cover += terrain.cover * (pos_bound - min_pos)  # Overlap interval width
                min_pos = pos_bound
        return cover

    def get_mean_scaled_roughness(self, file: int, pos: float, smooth_desire: float) -> float:
        file_map = self.terrain_map.get(file, {})
        min_pos, max_pos = pos-0.5, pos+0.5
        roughness = 0.0
        for pos_bound, terrain in file_map.items():

            if max_pos <= pos_bound:
                change = -terrain.roughness * smooth_desire * (max_pos - min_pos)
                roughness += 0 if (terrain.penalty and change > 0) else change
                break

            elif min_pos <= pos_bound:
                change = -terrain.roughness * smooth_desire * (pos_bound - min_pos)
                roughness += 0 if (terrain.penalty and change > 0) else change
                min_pos = pos_bound

        return roughness

    # File is a float rather than int here for drawing purposes
    def get_height(self, file: float, pos: float) -> float:
        ref_points = self.sort_nearest_points(file, pos)
        num_points = len(ref_points)

        if num_points == 0:
            return 0  # Absolute default
        elif num_points == 1:
            return ref_points[0][-1]  # Forced default
        elif (file, pos) in self.height_map:
            return self.height_map[(file, pos)]  # Don't interpolate if at an exact point
        else:
            # Standard case - interpolates using up to maximum number of points
            return self._calc_height(file, pos, ref_points[:self.MAX_HEIGHT_INTERPOL])

    def _calc_height(self, file: float, pos: float, ref_points: list[tuple[float, float, float]]
                     ) -> float:
        """Height is the weighted average of the height of the nearest points, where the weight
        is the inverse square of distance. Doing this quadratically makes nicely hills rounded"""
        numerator = 0.0
        denominator = 0.0
        for x, y, h in ref_points:
            w = 1/self.calc_sep_square(file, pos, x, y)
            numerator += w * h
            denominator += w
        return numerator / denominator

    def sort_nearest_points(self, file: float, pos: float) -> list[tuple[float, float, float]]:
        if len(self.height_map) <= self.MAX_HEIGHT_INTERPOL:  # No need to sort if few enough points
            return [(x, y, h) for (x, y), h in self.height_map.items()]

        return sorted([(x, y, h) for (x, y), h in self.height_map.items()],
                      key=lambda arg: self.calc_sep_square(file, pos, arg[0], arg[1]))

    def calc_sep_square(self, file_A: float, pos_A: float, file_B: float, pos_B: float) -> float:
        return ((file_A-file_B)*FILE_WIDTH)**2 + (pos_A-pos_B)**2
