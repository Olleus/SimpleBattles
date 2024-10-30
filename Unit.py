"""Definitions of units, the different types of units, and the armies they form"""
from itertools import chain
from math import log
from typing import Callable, Iterable, Self

from attrs import define, Factory, field, validators

from Config import DELTA_T
from Geography import Landscape
from Globals import RESERVE_FRC_BEHIND, MIN_DEPLOY_DIST, SIDE_RANGE_PENALTY, \
                    BASE_SPEED, CHARGE_DISTANCE, HALT_POWER_GRADIENT, \
                    TERRAIN_POWER, HEIGHT_DIF_POWER, RESERVES_POWER, RESERVES_SOFT_CAP, Stance


@define(frozen=True)
class UnitType:
    """The different types of units that can exist"""
    name: str
    power: float  # O(100)
    rigidity: float = field(default=0, validator=validators.gt(-1))  # O(1)
    speed: float = field(default=1, validator=validators.gt(0))  # O(1)
    att_range: float = field(default=1, validator=validators.ge(1))  # O(1)
    all_sides: bool = field(default=False)  # If true can attack any file (quadratic range penalty)
    pow_range: float = field()

    @pow_range.default
    def _default_pow_range(self) -> float:
        return 0 if self.att_range == 1 else self.power

    def __attrs_post_init__(self) -> None:
        if self.att_range == 1 and self.pow_range > 0:
            raise ValueError("Units with melee range cannot have a ranged power")
        if self.att_range > 1 and self.pow_range == 0:
            raise ValueError("Unit with an attack range must have ranged power")

    def __repr__(self) -> str:
        return f"{self.name: <10}  |  {self.power:.0f} P  "\
               f"{self.pow_range:.0f} ({self.att_range:.0f}) R  |  "\
               f"{self.rigidity:.2f} Rgd,  {self.speed:.0f} S"

    @property
    def smooth_desire(self) -> float: return self.rigidity + (self.speed - 1)
    @property
    def melee(self) -> bool: return self.att_range == 1
    @property
    def mixed(self) -> bool: return self.att_range > 1 and self.power > self.pow_range
    @property
    def ranged(self) -> bool: return self.att_range > 1 and self.power <= self.pow_range


@define(eq=False)
class Unit:
    """A specific unit that exists wthin an actual army"""
    # Class Attribute, use to prevent floating point errors
    POS_DEC_DIG = 3         # Position is rounded to this many decimal places
    EPS = 0.1 ** 3          # Max rounding error, used to push rounding one way or the other

    unit_type: UnitType
    stance: Stance
    file: int
    init_pos: float = field(init=False, default=0)
    landscape: Landscape | None = field(init=False, repr=False)

    # Vary continuously
    _position: float = field(init=False, default=0)
    morale: float = field(init=False, default=1)
    forced_move_towards: Self | None = field(init=False, default=None, repr=False)
    halted: bool = field(init=False, default=False)

    def __str__(self) -> str:
        return self.str_in_battle(lambda unit: 0, lambda unit: unit.morale)

    def str_in_battle(
            self, power_func: Callable[[Self], float], morale_func: Callable[[Self], float]) -> str:
        extra = power_func(self)
        pow_range = self.pow_range+extra if self.pow_range else 0
        return f"{self.name:<10} | {self.power+extra:<5.1f} P  {pow_range:<5.1f} R  " \
               f"{100*morale_func(self):<5.1f} M  |  " \
               f"({self.file:>2}, {self.position: .3f}, {self.height:.2f})"

    ##########################
    """ ATTRIBUTES & UTILS """
    ##########################

    @property
    def name(self) -> str: return self.unit_type.name
    @property
    def power(self) -> float: return self.unit_type.power
    @property
    def speed(self) -> float: return self.unit_type.speed
    @property
    def rigidity(self) -> float: return self.unit_type.rigidity
    @property
    def att_range(self) -> float: return self.unit_type.att_range
    @property
    def pow_range(self) -> float: return self.unit_type.pow_range
    @property
    def all_sides(self) -> bool: return self.unit_type.all_sides
    @property
    def smooth_desire(self) -> float: return self.unit_type.smooth_desire
    @property
    def melee(self) -> bool: return self.unit_type.melee
    @property
    def mixed(self) -> bool: return self.unit_type.mixed
    @property
    def ranged(self) -> bool: return self.unit_type.ranged
    @property
    def moving_to_pos(self) -> bool: return self.init_pos < 0
    @property
    def moving_to_neg(self) -> bool: return self.init_pos > 0
    @property
    def at_home(self) -> bool: return self.position == self.init_pos
    @property
    def at_end(self) -> bool: return self.position == -self.init_pos
    @property
    def position(self) -> float: return self._position

    @position.setter
    def position(self, value: float):
        position = max(-abs(self.init_pos), min(value, abs(self.init_pos)))
        self._position = round(position, self.POS_DEC_DIG)

    @property
    def height(self) -> float:
        return self.landscape.get_height(self.file, self.position) if self.landscape else 0

    @property
    def cover_from_terrain(self) -> float:
        return self.landscape.get_mean_cover(self.file, self.position) if self.landscape else 0

    @property
    def power_from_terrain(self) -> float:
        if not self.landscape:
            return 0
        rgh = self.landscape.get_mean_scaled_roughness(self.file, self.position, self.smooth_desire)
        return rgh*TERRAIN_POWER + self.height*HEIGHT_DIF_POWER

    @property
    def eff_speed(self) -> float:
        if not self.landscape:
            return self.speed
        return self.speed * (1 - self.landscape.get_terrain(self.file, self.position).roughness)

    def get_dist_to(self, position: float) -> float:
        return abs(self.position - position)

    ###############
    """ QUERIES """
    ###############

    def is_in_front(self, unit: Self) -> bool:
        return self.file == unit.file

    def is_in_range_of(self, unit: Self, melee: bool = False) -> bool:
        eff_range = self.get_eff_range_against(unit, melee)
        return self.get_dist_to(unit.position) <= eff_range + self.EPS/2

    def is_in_charge_range_of(self, target_pos: float) -> bool:
        return self.get_dist_to(target_pos) <= self.speed * CHARGE_DISTANCE + self.EPS/2

    def get_signed_distance_to_unit(self, unit: Self) -> float:
        """Positive means the other unit is ahead of it, according to this unit's direction"""
        return unit.position-self.position if self.moving_to_pos else self.position-unit.position

    def get_eff_range_against(self, unit: Self, melee: bool = False) -> float:
        base_range = 1 if melee else self.att_range
        return base_range - self.get_range_penalty_against(unit)

    def get_range_penalty_against(self, unit: Self) -> float:
        return abs(self.file - unit.file)**2 * SIDE_RANGE_PENALTY

    def get_position_to_attack_target(self, unit: Self, melee: bool = False) -> float:
        eff_range = self.get_eff_range_against(unit, melee)
        if self.position < unit.position - eff_range:    # Need to move forwards
            return unit.position - eff_range
        elif self.position > unit.position + eff_range:  # Need to move backwards
            return unit.position + eff_range
        else:                                            # No need to move at all
            return self.position

    def set_if_force_move_towards(self, target: Self, one_way: bool) -> None:
        melee_preference = (self.power - target.power) - (self.pow_range - target.pow_range)

        if self.is_in_range_of(target, melee=True):
            return
        if self.ranged or self.stance is Stance.DEF:
            return
        if self.melee or self.stance is Stance.AGG:
            self.forced_move_towards = target
            return
        # self is Mixed and Neutral for all branches below here
        if target.ranged:
            self.forced_move_towards = target
            return
        if target.melee:
            return
        # target is Mixed for all remaining branches
        if melee_preference > 0:
            self.forced_move_towards = target
            return
        if melee_preference < 0:
            return
        if one_way and not self.is_in_front(target):
            self.forced_move_towards = target
            return

    #########################
    """ ALTERING POSITION """
    #########################

    def set_up(self, init_pos: float, landscape: Landscape) -> None:
        self.init_pos = init_pos
        self.position = init_pos + self.EPS*(1 if self.moving_to_pos else -1)
        self.landscape = landscape
    
    def move_towards(self, target: float, speed: float) -> None:
        if self.position < target:
            self.position = min(self.position + speed*BASE_SPEED*DELTA_T, target)

        elif self.position > target:
            self.position = max(self.position - speed*BASE_SPEED*DELTA_T, target)

    def deploy_close_to(self, file: int, ref_pos: float):
        self.file = file
        dist = RESERVE_FRC_BEHIND * abs(self.init_pos)
        if self.moving_to_pos:
            self.position = max(ref_pos - dist, self.init_pos + MIN_DEPLOY_DIST)
        else:
            self.position = min(ref_pos + dist, self.init_pos - MIN_DEPLOY_DIST)

    def move_safely_away_from_pos(self, ref_pos: float) -> None:
        # Prevents overlapping units, jumps towards home as necessary
        if self.position < ref_pos + 1 and self.moving_to_neg:
            self.position = ref_pos + 1
        elif self.position > ref_pos - 1 and self.moving_to_pos:
            self.position = ref_pos - 1

    def confirm_move(self, gradient: float, old_pos: float, old_lag: float, new_lag: float) -> None:
        """Undoes movement if it weakens the unit too much, otherwise allows it"""
        if self.get_dist_to(self.init_pos) < MIN_DEPLOY_DIST:  # Too close to start to stop
            self.halted = False
            return

        if old_lag < 1 <= new_lag:  # Moved ahead of friendly flankers
            self.position = old_pos
            self.halted = True
            return

        # Increases percieved power gradient if moving away from supporting units
        new_lag = max(0, min(new_lag, 0.99))  # Prevent /0 or sign errors
        gradient *= 1/(1-new_lag) if old_lag < new_lag else 1

        if gradient > HALT_POWER_GRADIENT:  # Modified power desirability dropping too fast
            self.position = old_pos
            self.halted = True
        elif self.position != old_pos:  # Actually moved
            self.halted = False


@define(eq=False)
class Army:
    """A collection of units in various roles, as one of two in a battle"""

    name: str
    stance: Stance
    color: str = field(default="Black")  # Must match HTML color names
    file_units: dict[int, Unit] = field(init=False, default=Factory(dict))
    reserves: list[Unit] = field(init=False, default=Factory(list))
    removed: list[Unit] = field(init=False, default=Factory(list))

    def __str__(self) -> str:
        return self.str_in_battle(lambda unit: 0, lambda unit: unit.morale)

    def str_in_battle(
            self, power_func: Callable[[Unit], float], morale_func: Callable[[Unit], float]) -> str:
        string = f"{self.name} in {self.stance.name}"
        for file, unit in self.file_units.items():
            string += f"\n    {file:>2}: {unit.str_in_battle(power_func, morale_func)}"
        if self.reserves:
            string += "\n    Reserves:"
            for unit in self.reserves:
                string += f"\n        {unit}"
        if self.removed:
            string += "\n    Removed: "
            for unit in self.removed:
                string += f"{unit.name}    "
        return string

    ##################
    """ ATTRIBUTES """
    ##################

    @property
    def deployed_units(self) -> Iterable[Unit]: return self.file_units.values()
    @property
    def defeated(self) -> bool: return not self.file_units

    @property
    def reserve_power(self) -> float:
        """ = RESERVES_POWER * total_reserve_power / mean_deployed power, when
        total_reserve_power << RESERVES_SOFT_CAP * mean power, diminishing returns after:
        ~30% when total = soft_cap * mean, 50% when total ~= 2.5*soft_cap*mean
        """
        norm = sum(max(unit.power, unit.pow_range) for unit in self.deployed_units)
        norm /= len(self.file_units)
        total = sum(max(unit.power, unit.pow_range) for unit in self.reserves)
        return RESERVES_POWER * RESERVES_SOFT_CAP * log(1 + total / (norm*RESERVES_SOFT_CAP))

    @property
    def army_reach(self) -> float:
        return max((x.att_range + 2*x.speed for x in self.deployed_units), default=1)

    ###############
    """ QUERIES """
    ###############
    # FILES
    def is_file_active(self, file: int) -> bool:
        return file in self.file_units

    def get_centrewise_file(self, file: int) -> int:
        assert file != 0, "Central file does not have a central side"
        return file+1 if file < 0 else file-1

    # SPEED
    def get_aggressive_speed(self, unit: Unit, pos_target) -> float:
        """Own speed, reduced to backwards neighbor if pulling too far ahead"""
        quick = unit.eff_speed
        if unit.moving_to_pos and pos_target < unit.position:
            return quick
        if unit.moving_to_neg and pos_target > unit.position:
            return quick

        backwards_unit = self.get_backwards_neighbor(unit)
        if not backwards_unit:
            return quick

        slow = backwards_unit.eff_speed
        coef = 1 / (1 + abs(unit.position - backwards_unit.position))  # (0, 1]
        return coef*quick + (1-coef)*slow

    def get_cohesive_speed(self, unit: Unit, pos_target: float) -> float:
        """If moving backwards go at own speed, otherwise limit to slowest speed of lagging units"""
        if unit.moving_to_pos and pos_target < unit.position:
            return unit.eff_speed
        elif unit.moving_to_neg and pos_target > unit.position:
            return unit.eff_speed
        else:
            return self.get_minimum_laggard_speed(unit)

    def get_minimum_laggard_speed(self, unit: Unit) -> float:
        # No need for default, because the unit itself should always be in the loop
        return min((x.eff_speed for x in self.deployed_units
                    if x.get_dist_to(x.init_pos) <= unit.get_dist_to(unit.init_pos)))

    # UNITS
    def get_blocking_unit(self, enemy: Unit) -> Unit | None:
        """Which unit would the enemy first encounter, if any"""
        def sort_key(enemy, unit):
            dist = unit.get_dist_to(enemy.position)
            return dist + unit.get_range_penalty_against(enemy)

        if enemy.all_sides:
            neighbors = self.deployed_units
        else:
            neighbors = self.get_neighbors(enemy.file, include_self=True)

        return min(neighbors, key=lambda unit: sort_key(enemy, unit), default=None)

    def get_backwards_neighbor(self, ref_unit: Unit) -> Unit | None:
        """Which unit adjacent to the given one is furthest back, if any"""
        neighbors = self.get_neighbors(ref_unit.file, include_self=True)
        unit = min(neighbors, key=lambda unit: unit.get_dist_to(unit.init_pos), default=None)
        return None if unit is ref_unit else unit  

    def get_neighbors(self, file: int, include_self: bool = False) -> Iterable[Unit]:
        if include_self and self.is_file_active(file):  # Place first for sorting priority
            yield self.file_units[file]

        if self.is_file_active(file - 1):
            yield self.file_units[file - 1]

        if self.is_file_active(file + 1):
            yield self.file_units[file + 1]

    ################
    """ ALTERERS """
    ################

    def add(self, file: int, unit_type: UnitType) -> Self:
        self.file_units[file] = Unit(unit_type, self.stance, file)
        return self

    def add_reserves(self, *unit_type_args: UnitType) -> Self:
        for unit_type in unit_type_args:
            self.reserves.append(Unit(unit_type, self.stance, 0))
        return self

    def set_up(self, init_pos: float, landscape: Landscape) -> None:
        self.file_units = dict(sorted(self.file_units.items()))  # Sorting by file convenient
        for unit in chain(self.deployed_units, self.reserves, self.removed):
            unit.set_up(init_pos, landscape)

    def change_all_units_morale(self, change: float) -> None:
        for unit in chain(self.deployed_units, self.reserves):
            unit.morale += change

    def remove_unit(self, unit: Unit, other_army: Self) -> None:
        file = unit.file
        assert self.file_units[file] is unit, "Cannot remove a non deployed unit"
        del self.file_units[file]
        self.removed.append(unit)
        self.deploy_reserve_to_file(file, unit.position, other_army)

    def deploy_reserve_to_file(self, file: int, ref_pos: float, other_army: Self) -> None:
        if self.reserves:
            new_unit = self.reserves.pop(0)
            new_unit.deploy_close_to(file, ref_pos)
            other_army.move_unit_safely_away_from_enemy(new_unit)
            self.file_units[file] = new_unit

    def move_unit_safely_away_from_enemy(self, enemy: Unit) -> None:
        if enemy.file in self.file_units:
            self.file_units[enemy.file].move_safely_away_from_pos(enemy.position)

    def slide_to_new_file(self, old_file: int, new_file: int) -> None:
        self.file_units[new_file] = self.file_units[old_file]
        self.file_units[new_file].file = new_file
        del self.file_units[old_file]
