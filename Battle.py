"""Contains all logic for creating and resolving battles"""

from enum import Enum
from itertools import chain
from math import log
from typing import Any, Callable, Iterable, Self

from attrs import define, Factory, field, validators

import Config
from Geography import Landscape

# Internal computation
POS_DEC_DIG: int = 3             # Position is rounded to this many decimal places
EPS: float = 0.5 * (0.1 ** POS_DEC_DIG)  # Max error introduced by the above, use to force rounting
DELTA_T: float = Config.DELTA_T  # Used to scale how much movement / casualties are done per 'tick'

# Distance
# UNIT_HEIGHT = 1                # Height of all units
RESERVE_DIST_BEHIND: float = 2   # How far behind a defeated unit a reserve will deploy
MIN_DEPLOY_DIST: float = 1       # Closest to edge of the map that reserves will deploy
FAST_DISTANCE: float = 3         # Distance from enemy at which units in LINE become FAST
SIDE_RANGE_PENALTY: float = 0.5  # Range penalty when attacking adjacent file

# Movement
BASE_SPEED: float = 20           # Default unit speed
HALT_POWER_GRADIENT: float = 15  # Units in HOLD stop moving when power drops at this rate

# Power
POWER_SCALE: float = 50          # This much power difference results in a 2:1 casualty ratio
LOW_MORALE_POWER: float = 200    # Power applied is *[0, 1] from morale
TERRAIN_POWER: float = 300       # Power applied is *O(0.1)*O(0.1) from roughness and rigidity+speed
HEIGHT_DIF_POWER: float = 20     # Power applied is *O(0.1) from height difference
RESERVES_POWER: float = 1/6      # Rate at which reserves give their own power to deployed unit
RESERVES_SOFT_CAP: float = 500   # Scale which determines how sharply the above diminishes

PURSUE_MORALE: float = -0.25     # Morale loss inflicted when a unit starts pursing off the map
FILE_EMPTY: float = 0            # Morale for having an empty adjacent file
FILE_SUPPORTED: float = 0.1      # Morale for having an adjacent file protected by a friendly unit
FILE_VULNERABLE: float = -0.2    # Morale for having an adjacent file with a dangerously close enemy
FILE_MEAN: float = 0.5*(FILE_SUPPORTED+FILE_VULNERABLE)
FILE_DIFF: float = FILE_SUPPORTED - FILE_VULNERABLE


class BattleOutcome(Enum):
    """The different potential situation after the battle has concluded"""
    BOTH_LOST = 0   # Both armies end the battle with no remaining units
    WIN_1 = 1       # Army 1 wins by having remaining units while army 2 does not
    WIN_2 = 2       # Army 2 wins by having remaining units while army 1 does not
    STALEMATE = 3   # Both armies have units remaining, but timed out or will not engage


class Stance(Enum):
    """The lower number, the more aggressively the unit will move"""
    FAST = 0  # Moves at own speed always
    LINE = 1  # Moves at the slowest speed of the army
    HOLD = 2  # Same as LINE, but goes to HALT if moving would lower its power or break up the line 
    HALT = 3  # Same as Hold, but signals that last move was aborted


@define(frozen=True)
class UnitType:
    """The different types of units that can exist"""
    name: str
    power: float  # O(100)
    rigidity: float = field(default=0, validator=validators.gt(-1))  # O(1)
    speed: float = field(default=1, validator=validators.gt(0))  # O(1)
    att_range: float = field(default=1.0, validator=validators.ge(1))  # O(1)

    def __repr__(self) -> str:
        return f"{self.name: <10}  |  P={self.power:.0f} ({self.att_range:.0f}),  "\
               f"R={self.rigidity:.2f},  S={self.speed:.0f}"


@define(eq=False)
class Unit:
    """A specific unit that exists wthin an actual army"""
    unit_type: UnitType
    stance: Stance
    file: int
    init_pos: float = field(init=False, default=0)
    position: float = field(init=False, default=0)
    morale: float = field(init=False, default=1)
    pursuing: bool = field(init=False, default=False)

    def __str__(self) -> str:
        return f"{self.name:<10} | {self.power:<5.1f}P  {100*self.morale:<5.1f}M | " \
               f"({self.file:>2}, {self.position: .3f})"

    def str_in_battle(self, battle: "Battle") -> str:
        return f"{self.name:<10} | " \
               f"{battle.get_unit_eff_power(self):<5.0f}P  "\
               f"{100*battle.get_unit_eff_morale(self):<5.1f}M | " \
               f"({self.file:>2}, {self.position: .3f}, {self.get_height(battle.landscape):.2f})"

    ##########################
    """ ATTRIBUTES & UTILS """
    ##########################

    @property
    def name(self) -> str:
        return self.unit_type.name

    @property
    def power(self) -> float:
        return self.unit_type.power

    @property
    def speed(self) -> float:
        return self.unit_type.speed

    @property
    def rigidity(self) -> float:
        return self.unit_type.rigidity

    @property
    def att_range(self) -> float:
        return self.unit_type.att_range

    @property
    def smoothness_desire(self) -> float:
        return self.rigidity + (self.speed - 1)

    @property
    def moving_to_pos(self):
        return self.init_pos < 0

    @property
    def moving_to_neg(self):
        return self.init_pos > 0

    @property
    def at_home(self):
        return self.position == self.init_pos

    @property
    def at_end(self):
        return self.position == -self.init_pos

    def get_dist_to(self, position: float) -> float:
        return abs(self.position - position)

    ###############
    """ QUERIES """
    ###############

    # WITH RESPECT TO OTHER UNITS
    def is_in_front(self, unit: Self) -> bool:
        return self.file == unit.file

    def is_in_range_of(self, unit: Self) -> bool:
        if self.file is None or unit.file is None:
            return False
        return self.get_dist_to(unit.position) <= self.get_eff_range_against(unit) + EPS

    def get_position_to_attack_target(self, unit: Self) -> float:
        eff_range = self.get_eff_range_against(unit) - EPS
        if self.position < unit.position - eff_range:    # Need to move forwards
            return unit.position - eff_range
        elif self.position > unit.position + eff_range:  # Need to move backwards
            return unit.position + eff_range
        else:                                            # No need to move at all
            return self.position

    def get_eff_range_against(self, unit: Self) -> float:
        return self.att_range if unit.file == self.file else self.att_range - SIDE_RANGE_PENALTY

    def get_signed_distance_to_unit(self, unit: Self) -> float:
        """Positive means the other unit is ahead of it, according to this unit's direction"""
        dist = unit.position - self.position
        return dist if self.moving_to_pos else -dist

    # WITH RESPECT TO LANDSCAPE
    def get_height(self, landscape: Landscape) -> float:
        return landscape.get_height(self.file, self.position)

    def get_eff_speed(self, landscape: Landscape) -> float:
        return self.speed * (1 - landscape.get_terrain(self.file, self.position).roughness)

    def get_power_from_terrain(self, landscape: Landscape) -> float:
        rghn = landscape.get_mean_scaled_roughness(self.file, self.position, self.smoothness_desire)
        return rghn*TERRAIN_POWER + self.get_height(landscape)*HEIGHT_DIF_POWER

    #####################
    """ BASIC SETTERS """
    #####################

    def set_up(self, init_pos: float) -> None:
        self.init_pos = init_pos
        self.position = init_pos + (EPS if self.moving_to_pos else -EPS)

    def move_by(self, dist: float) -> None:
        self.position += dist
        self.cap_position()

    def move_to(self, position: float) -> None:
        self.position = position
        self.cap_position()

    def cap_position(self) -> None:
        self.position = round(capped(-abs(self.init_pos), self.position, abs(self.init_pos)),
                              POS_DEC_DIG)

    def change_stance_from_enemy_distance(self, dist: float, landscape: Landscape) -> None:
        if self.stance is Stance.LINE:
            if dist < self.get_eff_speed(landscape) * FAST_DISTANCE:
                self.stance = Stance.FAST

    def _change_morale(self, change: float) -> None:
        # Do not call directly, use army.change_unit_morale
        self.morale += change
        if change < 0:
            self.stance = Stance.FAST

    ########################
    """ COMPLEX MOVEMENT """
    ########################

    def move_towards_haltingly(self, target: float, speed: float, backwards_unit: Self | None,
                               desirability_method: Callable[[Self], float]) -> None:
        """Confirm movement only if it does not reduce desire or increase distance from supporting
        units on the flanks too much"""
        old_pos = self.position
        old_desire = desirability_method(self)
        old_lag = self.get_dist_to(backwards_unit.position) if backwards_unit else 0

        self.move_towards(target, speed)

        new_desire = desirability_method(self)
        new_lag = self.get_dist_to(backwards_unit.position) if backwards_unit else 0
        power_grad = (old_desire - new_desire) / self.get_dist_to(old_pos)

        self.confirm_move(power_grad, old_pos, old_lag, new_lag)

    def confirm_move(self, gradient: float, old_pos: float, old_lag: float, new_lag: float) -> None:
        """Undoes movement if it weakens the unit too much, otherwise allows it"""
        if self.get_dist_to(self.init_pos) < MIN_DEPLOY_DIST:
            self.stance = Stance.HOLD

        elif old_lag < 1 <= new_lag:
            self.position = old_pos
            self.stance = Stance.HALT

        else:
            # Increases percieved power gradient if moving away from supporting units
            gradient *= 1/(1-new_lag) if old_lag < new_lag else 1

            if gradient > HALT_POWER_GRADIENT:
                self.position = old_pos
                self.stance = Stance.HALT

            elif self.position != old_pos:
                self.stance = Stance.HOLD
    
    def move_towards(self, target: float, speed: float) -> None:
        if self.position < target:
            self.move_to(min(self.position + speed*BASE_SPEED*DELTA_T, target))

        elif self.position > target:
            self.move_to(max(self.position - speed*BASE_SPEED*DELTA_T, target))

    def deploy_close_to(self, file: int, ref_pos: float):
        self.file = file

        # Give some breathing room to reserve units when deployed
        if self.moving_to_pos:
            position = max(ref_pos - RESERVE_DIST_BEHIND, self.init_pos + MIN_DEPLOY_DIST)
        else:
            position = min(ref_pos + RESERVE_DIST_BEHIND, self.init_pos - MIN_DEPLOY_DIST)
        self.move_to(position)

    def move_safely_away_from_pos(self, ref_pos: float) -> None:
        # Prevents overlapping units, jumps towards home as necessary
        if self.position < ref_pos + 1 and self.moving_to_neg:
            self.move_to(ref_pos + 1)
        elif self.position > ref_pos - 1 and self.moving_to_pos:
            self.move_to(ref_pos - 1)


@define(eq=False)
class Army:
    """A collection of units in various roles, as one of two in a battle"""
    # VALIDATOR
    def valid_army_stance(self, attribute, value):
        if value is Stance.HALT:
            raise ValueError("Army should not being in the HALT stance")

    name: str
    stance: Stance = field(validator=valid_army_stance)
    color: str = field(default="Black")  # Must match HTML color names
    file_units: dict[int, Unit] = field(init=False, default=Factory(dict))
    reserves: list[Unit] = field(init=False, default=Factory(list))
    removed: list[Unit] = field(init=False, default=Factory(list))

    def __str__(self) -> str:
        string = f"{self.name}"
        for file, unit in self.file_units.items():
            string += f"\n    {file:>2}: {unit}"
        if self.reserves:
            string += "\n    Reserves:"
            for unit in self.reserves:
                string += f"\n        {unit}"
        if self.removed:
            string += "\n    Removed: "
            for unit in self.removed:
                string += f"{unit.name}    "
        return string

    def str_in_battle(self, battle: "Battle") -> str:
        string = f"{self.name}"
        for file, unit in self.file_units.items():
            string += f"\n    {file:>2}: {unit.str_in_battle(battle)}"
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
    def units(self) -> Iterable[Unit]:
        return chain(self.deployed_units, self.reserves, self.removed)

    @property
    def deployed_units(self) -> Iterable[Unit]:
        return self.file_units.values()

    @property
    def defeated(self) -> bool:
        return not self.file_units

    @property
    def reserve_power(self) -> float:
        """reserve_power ~= RESERVES_POWER*total when total far below soft cap, with a drop of:
        ~30% when total = soft_cap, 50% when total ~= 2.5*soft_cap
        """
        total = sum(unit.power for unit in self.reserves)
        return RESERVES_POWER * RESERVES_SOFT_CAP * log(1 + total/RESERVES_SOFT_CAP)

    ###############
    """ QUERIES """
    ###############

    # Over whole army
    def get_army_reach(self) -> float:
        return 1 + max((x.att_range + 2*x.speed for x in self.deployed_units), default=3)

    def get_communal_eff_speed(self, landscape: Landscape) -> float:
        """Slowest eff_speed, further reduced by fraction of units in Stance.HOLD"""
        return min((unit.get_eff_speed(landscape) for unit in self.deployed_units
                    if unit.stance is not Stance.FAST), default=1)

    # Over file and its neighbors
    def get_blocking_unit(self, enemy: Unit) -> Unit | None:
        """Which unit would the enemy) first encounter, if any"""
        ordered_units: dict[float, Unit] = {}

        for side in [-1, +1, 0]:  # In this order, because last one overwrites others
            if self.is_file_active(enemy.file + side):
                unit = self.file_units[enemy.file + side]
                dist = unit.get_dist_to(enemy.position) + (0 if side == 0 else SIDE_RANGE_PENALTY)
                ordered_units[dist] = unit

        return ordered_units[min(ordered_units)] if ordered_units else None

    def get_backwards_neighbor(self, ref_unit: Unit) -> Unit | None:
        """Which unit adjacent to the given one is furthest back"""
        ordered_units: dict[float, Unit] = {}

        for side in [-1, +1]:
            if self.is_file_active(ref_unit.file + side):
                unit = self.file_units[ref_unit.file + side]
                dist = unit.get_dist_to(ref_unit.init_pos)
                ordered_units[dist] = unit

        return ordered_units[min(ordered_units)] if ordered_units else None

    def is_file_active(self, file: int) -> bool:
        return file in self.file_units

    def is_file_towards_centre_active(self, file: int) -> bool:
        assert file != 0, "Central file does not have a central side"
        return self.is_file_active(file+1 if file < 0 else file-1)

    #####################
    """ BASIC SETTERS """
    #####################

    def add(self, file: int, unit_type: UnitType) -> Self:
        self.file_units[file] = Unit(unit_type, self.stance, file)
        return self

    def add_reserves(self, *unit_type_args: UnitType) -> Self:
        for unit_type in unit_type_args:
            self.reserves.append(Unit(unit_type, Stance.FAST, 0))
        return self

    def set_up(self, init_pos: float) -> None:
        self.file_units = dict(sorted(self.file_units.items()))  # Sorting by file convenient
        for unit in self.units:
            unit.set_up(init_pos)

    def change_all_units_morale(self, change: float) -> None:
        for unit in chain(self.deployed_units, self.reserves):
            self.change_unit_morale(unit, change)

    def change_unit_morale(self, unit: Unit, change: float) -> None:
        unit._change_morale(change)
        if change < 0:
            self.set_neighbors_to_FAST(unit.file)

    def set_neighbors_to_FAST(self, file: int) -> None:
        for new_file in [file-1, file+1]:
            if new_file in self.file_units:
                self.file_units[new_file].stance = Stance.FAST

    ################
    """ ALTERERS """
    ################

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
            unit = self.file_units[enemy.file]
            unit.move_safely_away_from_pos(enemy.position)

    def slide_file_towards_centre(self, file: int) -> None:
        assert not self.is_file_towards_centre_active(file)
        new_file = file+1 if file < 0 else file-1

        self.file_units[new_file] = self.file_units[file]
        self.file_units[new_file].file = new_file
        del self.file_units[file]


@define(eq=False)
class FightPairs:
    """Decides which units will attack which other units and stores this as lists of tuples"""
    army_1: Army
    army_2: Army
    _potentials: dict[Unit, set[Unit]] = field(init=False, default=Factory(dict))
    _assignments: dict[Unit, Unit] = field(init=False, default=Factory(dict))
    two_way_pairs: list[tuple[Unit, Unit]] = field(init=False, default=Factory(list))
    one_way_pairs: list[tuple[Unit, Unit]] = field(init=False, default=Factory(list))

    def reset(self) -> None:
        self._potentials = {}
        self._assignments = {}
        self.two_way_pairs = []
        self.one_way_pairs = []

    def assign_all(self) -> None:
        self.reset()
        self.add_all_potentials()
        self.assign_if_unique_target()
        while self._potentials:
            self.assign_best_remaining()
        self.match_into_pairs()

    def add_all_potentials(self) -> None:
        for file, unit in self.army_1.file_units.items():
            self.add_single_potentials(file, unit, self.army_2)

        for file, unit in self.army_2.file_units.items():
            self.add_single_potentials(file, unit, self.army_1)

    def add_single_potentials(self, file: int, unit: Unit, opposing: Army) -> None:
        targets: set[Unit] = set()
        targets |= self.get_valid_targets(file, unit, opposing)  
        targets |= self.get_valid_targets(file - 1, unit, opposing)  
        targets |= self.get_valid_targets(file + 1, unit, opposing)        

        if targets:
            self._potentials[unit] = targets

    def get_valid_targets(self, file: int, unit: Unit, opposing: Army) -> set[Unit]:
        if file in opposing.file_units:
            target = opposing.file_units[file]
            if unit.is_in_range_of(target):
                return {target}
        return set()

    def assign_if_unique_target(self) -> None:
        for unit, targets in list(self._potentials.items()):
            if len(targets) == 1:
                self._assignments[unit] = list(targets)[0]
                del self._potentials[unit]

    def assign_best_remaining(self) -> None:
        assigned_to = invert_dictionary(self._assignments)

        def sort_key(unit, target):
            """Lots of trial and error needed to get this behaving sensibly - tread lightly
                (Recall that True > False)"""
            frontal = unit.is_in_front(target)
            dist = unit.get_dist_to(target.position) - EPS
            melee = (dist <= 1) if frontal else (dist <= 1 - SIDE_RANGE_PENALTY)
            attacker = target in assigned_to.get(unit, set())
            unassigned = target not in self._assignments

            return (frontal and melee,                                         # Always do if true
                    melee, frontal, attacker, unassigned,                      # Top rank priorities
                    -dist, -unit.att_range, abs(unit.file), abs(target.file),  # Remaing priorities
                    unit.file, target.file, unit.position)                     # Breaks any ties

        score, unit, target = max((sort_key(att, x), att, x)
                                  for att in self._potentials for x in self._potentials[att])

        self._assignments[unit] = target
        del self._potentials[unit]

    def match_into_pairs(self) -> None:
        remaining = set(self._assignments)

        while remaining:
            unit_A = remaining.pop()
            unit_B = self._assignments[unit_A]
            if unit_A is self._assignments.get(unit_B, None):
                self.two_way_pairs.append((unit_A, unit_B))
                remaining.remove(unit_B)
            else:
                self.one_way_pairs.append((unit_A, unit_B))


@define(eq=False)
class Battle:
    """Top level class that holds references to everything"""
    army_1: Army
    army_2: Army
    landscape: Landscape
    fight_pairs: FightPairs = field(init=False)
    turns: int = field(init=False, default=0)

    @fight_pairs.default
    def _default_fight_pairs(self) -> FightPairs:
        return FightPairs(self.army_1, self.army_2)

    def __attrs_post_init__(self) -> None:
        init_pos = max(self.army_1.get_army_reach(), self.army_2.get_army_reach(), 5)
        self.army_1.set_up(-init_pos)
        self.army_2.set_up(init_pos)

    ###############
    """ QUERIES """
    ###############

    def iter_all_deployed(self) -> Iterable[Unit]:
        yield from self.army_1.deployed_units
        yield from self.army_2.deployed_units

    def get_army_deployed_in(self, unit: Unit) -> Army:
        if self.army_1.file_units.get(unit.file, None) is unit:
            return self.army_1
        elif self.army_2.file_units.get(unit.file, None) is unit:
            return self.army_2
        else:
            raise ValueError(f"{unit} is not deployed in Battle")

    def get_other_army(self, army: Army) -> Army:
        if army is self.army_1:
            return self.army_2
        elif army is self.army_2:
            return self.army_1
        else:
            raise ValueError(f"{army} is not in Battle")

    #################
    """ CORE LOOP """
    #################

    def do(self, verbosity: int) -> BattleOutcome:
        if verbosity >= 10:
            self.print_turn()

        while not self.is_battle_ended():
            self.turns += 1
            self.do_turn(verbosity)

        self.print_result(verbosity)
        return self.decide_winner()

    def do_turn(self, verbosity: int) -> None:
        self.tidy()
        self.fight()
        self.move()
        if verbosity >= 100:
            self.print_turn()
        # Drawing frame happens here - between a fight() and the next tidy()

    def is_battle_ended(self) -> bool:
        if self.army_1.defeated:
            return True
        if self.army_2.defeated:
            return True
        if all(unit.stance is Stance.HALT for unit in self.iter_all_deployed()):
            return True
        if self.turns > 1000:
            return True
        return False

    def decide_winner(self) -> BattleOutcome:
        if self.army_1.defeated and self.army_2.defeated:
            return BattleOutcome.BOTH_LOST
        elif not self.army_1.defeated and self.army_2.defeated:
            return BattleOutcome.WIN_1
        elif self.army_1.defeated and not self.army_2.defeated:
            return BattleOutcome.WIN_2
        else:
            return BattleOutcome.STALEMATE

    ############
    """ TIDY """
    ############

    def tidy(self) -> None:
        # Order important, need to change morale before changing files before marked as pursuing
        self.change_morale_from_first_pursue()
        self.reduce_files()
        self.update_status()

    def change_morale_from_first_pursue(self) -> None:
        for unit in self.iter_all_deployed():
            if unit.at_end:
                if not unit.pursuing:
                    other_army = self.get_other_army(self.get_army_deployed_in(unit))
                    other_army.change_all_units_morale(PURSUE_MORALE)

    def reduce_files(self) -> None:
        """If a unit is pursuing, has no adjacent enemies, and can slide towards centre; do so"""
        for unit in list(self.iter_all_deployed()):
            if unit.pursuing and unit.file != 0:
                army = self.get_army_deployed_in(unit)
                enemy = self.get_other_army(army).get_blocking_unit(unit)
                if enemy is None:
                    if not army.is_file_towards_centre_active(unit.file):
                        army.slide_file_towards_centre(unit.file)

    def update_status(self) -> None:
        for unit in list(self.iter_all_deployed()):

            if self.get_unit_eff_morale(unit) <= 0 or unit.at_home:
                army = self.get_army_deployed_in(unit)
                army.remove_unit(unit, self.get_other_army(army))

            elif unit.at_end and self.get_unit_eff_morale(unit) > 0:
                unit.pursuing = True

            else:
                unit.pursuing = False

    ################
    """ FIGHTING """
    ################

    def fight(self) -> None:
        self.fight_pairs.assign_all()

        for unit_A, unit_B in self.fight_pairs.two_way_pairs:
            self.fight_two_way(unit_A, unit_B)

        for unit_A, unit_B in self.fight_pairs.one_way_pairs:
            self.fight_one_way(unit_A, unit_B)

    def fight_two_way(self, unit_A: Unit, unit_B: Unit) -> None:
        self.change_stances_from_fight(unit_A, unit_B)
        balance = self.compute_fight_balance(unit_A, unit_B)
        self.inflict_casualties(unit_A, 1/balance)
        self.inflict_casualties(unit_B, balance)
        self.push_from_fight(unit_A, unit_B, balance)

    def fight_one_way(self, unit_A: Unit, unit_B: Unit) -> None:
        self.change_stances_from_fight(unit_A, unit_B)
        balance = self.compute_fight_balance(unit_A, unit_B)
        self.inflict_casualties(unit_B, balance)

    def change_stances_from_fight(self, unit_A: Unit, unit_B: Unit) -> None:
        unit_A.stance = Stance.FAST
        unit_B.stance = Stance.FAST

    def compute_fight_balance(self, unit_A: Unit, unit_B: Unit) -> float:
        power_dif = self.get_unit_eff_power(unit_A) - self.get_unit_eff_power(unit_B)
        return 2.0 ** (power_dif / (2*POWER_SCALE))

    def get_unit_eff_power(self, unit: Unit) -> float:
        power = unit.power
        power += unit.get_power_from_terrain(self.landscape)
        power += self.get_army_deployed_in(unit).reserve_power
        power += self.get_unit_power_from_morale(unit)
        return power

    def get_unit_power_from_morale(self, unit: Unit) -> float:
        return -LOW_MORALE_POWER * (1 - (self.get_unit_eff_morale(unit) ** (1+unit.rigidity)))

    def get_unit_eff_morale(self, unit: Unit) -> float:
        morale = unit.morale
        morale += self.get_morale_from_supporting_file(unit, unit.file+1)
        morale += self.get_morale_from_supporting_file(unit, unit.file-1)
        return max(0, morale)

    def get_morale_from_supporting_file(self, unit: Unit, file: int) -> float:
        army = self.get_army_deployed_in(unit)
        enemy = self.get_other_army(army)

        if enemy.is_file_active(file):
            return self._morale_from_contested_file(unit, file, army, enemy)
        elif army.is_file_active(file):
            return FILE_SUPPORTED
        else:
            return FILE_EMPTY

    def _morale_from_contested_file(self, unit: Unit, file: int, army: Army, enemy: Army) -> float:
        """If a file is contested, give morale according to a linear scale between fully supported
        and fuly contested, according to where a fictious "clash line" is on that file"""
        ene_dist = unit.get_signed_distance_to_unit(enemy.file_units[file])

        own_dist = -RESERVE_DIST_BEHIND  # If not friendly, assume this far behind
        if army.is_file_active(file):
            own_dist = max(own_dist, unit.get_signed_distance_to_unit(army.file_units[file]))

        """Mean is weighted towards the enemy: friendly units protect further than enemies threaten.
        Matches RESERVE_DIST_BEHIND such that flanking melee range just causes full vulnerablity
        when there are no supporting units"""
        weight = RESERVE_DIST_BEHIND - 0.5
        mean_dist = (weight*ene_dist + own_dist) / (1+weight)
        return self._morale_from_mean_clash_distance(mean_dist)

    def _morale_from_mean_clash_distance(self, mean_dist: float) -> float:
        if mean_dist > 0.5:
            return FILE_SUPPORTED
        elif mean_dist < -0.5:
            return FILE_VULNERABLE
        else:
            return FILE_MEAN + mean_dist*FILE_DIFF

    def inflict_casualties(self, unit: Unit, balance: float) -> None:
        cover = 1 - self.landscape.get_mean_cover(unit.file, unit.position)
        change = -DELTA_T * cover * balance
        self.get_army_deployed_in(unit).change_unit_morale(unit, change)

    def push_from_fight(self, unit_A: Unit, unit_B: Unit, balance: float) -> None:
        if balance > 1:    # A is pushing B back
            self._push_from_winner(unit_A, unit_B, balance)
        elif balance < 1:  # B is pusing A back
            self._push_from_winner(unit_B, unit_A, 1/balance)

    def _push_from_winner(self, winner: Unit, loser: Unit, balance: float) -> None:
        # Loser runs according to its speed, how badly it lost and rigidity, capped by winners speed
        loser_speed_scale = min(1, (balance-1) / (1+loser.rigidity))
        dist = min(winner.get_eff_speed(self.landscape),
                   loser.get_eff_speed(self.landscape) * loser_speed_scale)
        dist *= BASE_SPEED * DELTA_T * (1 if winner.moving_to_pos else -1)
        loser.move_by(dist)

        # Winner chases only if it keeps fiht active
        if not winner.is_in_range_of(loser) or not loser.is_in_range_of(winner):
            winner.move_by(dist)

    ##############
    """ MOVING """
    ##############

    def move(self) -> None:
        for unit in self.get_move_order():
            enemy = self.get_other_army(self.get_army_deployed_in(unit)).get_blocking_unit(unit)

            if not enemy:
                unit.stance = Stance.FAST  # Unit will never be attacked, so try to pursue ASAP
                self.move_unit_towards(unit, -unit.init_pos)

            elif not unit.is_in_range_of(enemy):
                dist = unit.get_dist_to(enemy.position)
                unit.change_stance_from_enemy_distance(dist, self.landscape)
                target_pos = unit.get_position_to_attack_target(enemy)
                self.move_unit_towards(unit, target_pos)

    def get_move_order(self) -> list[Unit]:
        """Move melee units in centre first (last two are to break tie)"""
        return sorted(self.iter_all_deployed(), key=lambda x:
                      (x.stance.value, x.att_range, abs(x.file), -abs(x.position),
                       x.file, x.position))

    def move_unit_towards(self, unit: Unit, target: float) -> None:
        speed = self.get_unit_advance_speed(unit)

        if unit.stance is Stance.FAST or unit.stance is Stance.LINE:
            unit.move_towards(target, speed)

        elif unit.stance is Stance.HOLD or unit.stance is Stance.HALT:
            backwards_unit = self.get_army_deployed_in(unit).get_backwards_neighbor(unit)
            unit.move_towards_haltingly(target, speed, backwards_unit, self.get_unit_pos_desire)

        else:
            raise ValueError(f"Unknown stance {unit.stance}")

    def get_unit_advance_speed(self, unit: Unit) -> float:
        if unit.stance is Stance.FAST:
            return unit.get_eff_speed(self.landscape)
        return self.get_army_deployed_in(unit).get_communal_eff_speed(self.landscape)

    def get_unit_pos_desire(self, unit: Unit) -> float:
        cover = self.landscape.get_mean_cover(unit.file, unit.position)
        return self.get_unit_eff_power(unit) + 10*cover 

    ################
    """ PRINTING """
    ################

    def print_result(self, verbosity: int) -> None:
        if verbosity > 0:
            if verbosity < 100:  # Don't reprint when verbosity is high
                self.print_turn()
            self.print_winner()

    def print_turn(self) -> None:
        print(f"\nTurn {self.turns}")
        self.print_fights()
        print(self.army_1.str_in_battle(self))
        print(self.army_2.str_in_battle(self))

    def print_fights(self) -> None:
        all_fights = self.fight_pairs.two_way_pairs + self.fight_pairs.one_way_pairs

        order = sorted(all_fights, key=lambda x: (x[0].file, x[1].file))
        if order:
            string = "  "
            for unit_A, unit_B in order:
                if self.get_army_deployed_in(unit_A) == self.army_1:
                    file_1, file_2 = unit_A.file, unit_B.file
                    arrow = "-->"
                else:
                    file_2, file_1 = unit_A.file, unit_B.file
                    arrow = "<--"
                if (unit_A, unit_B) in self.fight_pairs.two_way_pairs:
                    arrow = "<->"
                string += f"  {file_1} {arrow} {file_2}  |"
            print(string[:-3])

    def print_winner(self) -> None:
        winner = self.decide_winner()
        print(f"\nBattle lasted {self.turns} turns")
        if winner is BattleOutcome.STALEMATE:
            print("ARMIES FOUGHT TO A STALEMATE")
        elif winner is BattleOutcome.WIN_1:
            print(f"{self.army_1.name.upper()} WAS VICTORIOUS")
        elif winner is BattleOutcome.WIN_2:
            print(f"{self.army_2.name.upper()} WAS VICTORIOUS")
        elif winner is BattleOutcome.BOTH_LOST:
            print("NEITHER ARMY HELD THE FIELD")
        else:
            raise ValueError(f"Unknown result of battle {winner}")


def invert_dictionary(init: dict) -> dict:
    """ Takes {x1: y1, x2: y2, x3: y2, ...} and returns {y1: {x1}, y2: {x2, x3}, ....} """
    fin: dict[Any, Any] = {}
    for key, value in init.items():
        fin[value] = fin[value] | {key} if (value in fin) else {key}
    return fin


def capped(l_cap: float, y: float, u_cap: float) -> float:
    return max(l_cap, min(y, u_cap))
