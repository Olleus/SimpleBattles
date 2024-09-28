from functools import cache
from itertools import chain
from math import inf

from attrs import define, Factory, field, validators
from typing import Iterable, Self

# Floating point error prevention
POS_DEC_DIG: int = 3
EPS: float = 0.5 * (0.1 ** POS_DEC_DIG)

# Terrain Global
# UNIT_HEIGHT = 1    -    SETS THE SIZE SCALE  
FILE_WIDTH: float = 4  # Width of file in vertical length scale (also unit aspect ratio)

# Unit Globals
SIDE_RANGE_PENALTY: float = 0.5
BASE_SPEED: float = 20
PURSUE_MORALE: float = -0.1
HARASS_SLOW_DOWN: float = 1.5

LOW_MORALE_POWER: float = 200
TERRAIN_POWER: float = 100  # * O(1) * O(1)
NEIGHBOR_POWER: float = 10

# Army Global
LOCKED_SPEED_DIST: float = 4
FILE_EMPTY: int = 0
FILE_VULNERABLE: int = -2
FILE_SUPPORTED: int = 1
RESERVE_DIST_BEHIND: float = 2
MIN_RESERVE_DIST: float = 0.5

# Fight Global
POWER_SCALE: float = 50  # This much power difference results in a 2:1 casualty ratio
DELTA_T: float = 0.005  # 1 / DELTA_T is roughly num of turns in battle


@define(frozen=False)
class Terrain:

    name: str
    color: str = field(default="White")  # Must match HTML color names
    smoothness: float = field(default=0, validator=[validators.gt(-1), validators.lt(1)])
    cover: float = field(default=0, validator=[validators.gt(-1), validators.lt(1)])
    penalty: bool = field(default=False)  # If true, can smoothness can never increase value


DEFAULT_TERRAIN = Terrain("Undefined", "white", 0)


def is_inner_dict_sorted(instance, attribute, value):
    for inner in value.values():
        keys = list(inner.keys())
        if not keys == sorted(keys):
            raise ValueError("Keys in inner dict are not sorted as expected")


@define
class Landscape:
    """Landscape defined by giving Terrain at individual positions in files"""

    # Outer key is file, inner key gives terrain up to that position (from prior one)
    terrain_map: dict[int, dict[float, Terrain]] = field(
        converter=lambda x: dict(sorted(x.items())), validator=is_inner_dict_sorted)

    def terrain(self, file: int, pos: float) -> Terrain:
        file_map = self.terrain_map.get(file, {})
        for pos_bound, terrain in file_map.items():
            if pos < pos_bound:
                return terrain
        return DEFAULT_TERRAIN

    # DONT DELETE JUST YET - WILL USE FOR HEIGHT
    # terrain_map: dict[int, dict[float, Terrain]] = field(
    #     converter=lambda x: dict(sorted([(k, dict(sorted(v.items()))) for k, v in x.items()])))
    # # Converter sorts the dictionary by both file (outer) and position (inner)

    # def terrain(self, file: int, pos: float) -> Terrain:
    #     """Position of closest define terrain in file (ties broken towards the middle) """
    #     file_map = self.file_map(file)
    #     key = min(file_map, key=lambda x: (abs(x-pos), abs(x), x))
    #     return file_map[key]

    # def file_map(self, file: int) -> dict[float, Terrain]:
    #     """Guaranteed to never return an empty dict, even if empty dicts passed to terrain_map"""
    #     file_map = self.terrain_map.get(file, {})
    #     return file_map if file_map else {0: DEFAULT_TERRAIN}


@define(frozen=True)
class UnitType:

    name: str
    power: float  # ~100

    rigidity: float = field(default=0, validator=[validators.gt(-1), validators.lt(1)])
    speed: float = field(default=BASE_SPEED, validator=validators.gt(0))  # O(BASE_SPEED)
    att_range: float = field(default=1.0, validator=validators.ge(1.0))  # O(1)

    def __repr__(self) -> str:
        return f"{self.name: <10}  |  P={self.power:.0f} ({self.att_range:.0f}),  "\
               f"R={self.rigidity:.2f},  S={self.speed:.0f}"


@define(eq=False)
class Unit:

    # Set at Initialisation
    army: "Army"
    unit_type: UnitType
    file: int
    position: float = field(init=False, default=0)

    # Default
    morale: float = field(init=False, default=1)
    harassment: float = field(init=False, default=0)
    pursuing: bool = field(init=False, default=False)

    def __repr__(self) -> str:
        return f"{self.name:<10} | {self.eff_power():<5.1f}P  {100*self.morale:<5.1f}M | " \
               f"({self.file:>2}, {self.position: .3f})"

    # Pull up attributes to Unit
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
    def terrain(self) -> Terrain:
        return self.army.landscape.terrain(self.file, self.position)

    # New attributes
    @property
    def eff_speed(self) -> float:
        if self in self.army.deployed_units:
            eff_speed = self.speed*(1+self.terrain.smoothness) / (HARASS_SLOW_DOWN**self.harassment)
            return min(self.army.locked_speed, eff_speed)
        else:
            return self.speed

    @property
    def eff_terain_rigidity(self) -> float:
        return self.rigidity + (self.speed/BASE_SPEED - 1)

    # Getters
    def is_in_front(self, unit: Self) -> bool:
        return self.file == unit.file

    def is_in_range_of(self, unit: Self) -> bool:
        if self.file is None or unit.file is None:
            return False
        return self.distance_to(unit.position) <= self.eff_range_for(unit.file) + EPS

    def eff_range_for(self, file: int) -> float:
        return self.att_range if file == self.file else self.att_range - SIDE_RANGE_PENALTY

    def distance_to(self, position: float) -> float:
        return abs(self.position - position)

    def eff_power(self) -> float:
        if self in self.army.deployed_units:
            morale = -LOW_MORALE_POWER * (1 - (self.morale ** (1+self.rigidity)))
            neighbour = NEIGHBOR_POWER * self.state_neighboring_files() * (1+self.rigidity)
            terrain = TERRAIN_POWER * self.terrain.smoothness * self.eff_terain_rigidity
            terrain = min(0, terrain) if self.terrain.penalty else terrain
            return self.power + morale + neighbour + terrain
        else:
            return self.power

    def state_neighboring_files(self) -> int:
        """alone: -1, end of line: 0 (if open: -3), centre: 1, one flank open: -2, both open: -5"""
        if self in self.army.deployed_units:
            state = -1
            state += self.army.file_state(self.file - 1, self.position)
            state += self.army.file_state(self.file + 1, self.position)
            return state
        else:
            return 0

    # Setters
    def move_towards(self, target: float) -> None:
        if self.position < target:
            self.position = min(self.position + self.eff_speed*DELTA_T, target)

        elif self.position > target:
            self.position = max(self.position - self.eff_speed*DELTA_T, target)

        self.cap_position()

    def move_towards_range_of(self, unit: Self) -> None:
        target = unit.position
        eff_range = self.eff_range_for(unit.file) - EPS

        if self.position < target - eff_range:
            self.position = min(self.position + self.eff_speed*DELTA_T, target - eff_range)

        elif self.position > target + eff_range:
            self.position = max(self.position - self.eff_speed*DELTA_T, target + eff_range)

        self.cap_position()

    def move_by(self, dist: float) -> None:
        self.position += dist
        self.cap_position()

    def move_to(self, position: float) -> None:
        self.position = position
        self.cap_position()

    def cap_position(self) -> None:
        min_pos, max_pos = self.army.min_max_positions()
        self.position = round(capped(min_pos, self.position, max_pos), POS_DEC_DIG)

    def change_morale(self, change: float) -> None:
        self.morale = max(0, self.morale + change)

    def change_harassment(self, change: float) -> None:
        self.harassment = max(0, self.harassment + change)

    def update_status(self) -> None:
        self.harassment = 0

        if self.morale <= 0 or self.position == self.army.init_position:
            self.army.remove_unit(self)

        elif self.position == self.army.other_army.init_position:
            if not self.pursuing:
                self.army.other_army.change_morale(PURSUE_MORALE)
                self.pursuing = True


@define(eq=False)
class Army:

    name: str
    color: str = field(default="Black")  # Must match HTML color names

    file_units: dict[int, Unit] = field(init=False, default=Factory(dict))
    reserves: list[Unit] = field(init=False, default=Factory(list))
    removed: list[Unit] = field(init=False, default=Factory(list))

    init_position: float = field(init=False, default=0)
    locked_speed: float = field(init=False, default=inf)
    landscape: Landscape = field(init=False)
    other_army: Self = field(init=False)

    def __str__(self) -> str:
        string = f"Army (init_pos={self.init_position:.0f})"
        for file, unit in self.file_units.items():
            string += f"\n    {file:>2}: {unit}"
        if self.reserves:
            string += "\n    Reserves:"
            for unit in self.reserves:
                string += f"\n        {unit}"
        return string

    @property
    def units(self) -> Iterable[Unit]:
        return chain(self.file_units.values(), self.reserves, self.removed)

    @property
    def deployed_units(self) -> Iterable[Unit]:
        return self.file_units.values()

    @property
    def active(self) -> bool:
        return any(not unit.pursuing for unit in self.deployed_units)

    @property
    def defeated(self) -> bool:
        return len(self.file_units) == 0

    @cache
    def min_max_positions(self) -> list[float]:
        return sorted((self.init_position, self.other_army.init_position))

    # Creation
    def add(self, file: int, unit_type: UnitType) -> Self:
        self.file_units[file] = Unit(self, unit_type, file)
        return self

    def add_reserves(self, *unit_type_args: UnitType) -> Self:
        for unit_type in unit_type_args:
            self.reserves.append(Unit(self, unit_type, 0))
        return self

    def set_up(self, top: bool, landscape: Landscape, other_army: Self) -> None:
        assert len(self.file_units), "Cannot setup an army without any deployed units"
        self.file_units = dict(sorted(self.file_units.items()))
        self.set_up_init_position(top)
        self.landscape = landscape
        self.locked_speed = min(unit.eff_speed for unit in self.deployed_units)
        self.other_army = other_army

    def set_up_init_position(self, top: bool) -> None:
        self.init_position = max(max(1+x.att_range, 3*x.speed/BASE_SPEED)
                                 for x in self.deployed_units)
        self.init_position *= -1 if top else 1
        for unit in self.units:
            unit.position = self.init_position

    # Setters
    def update_status(self) -> None:
        for unit in list(self.deployed_units):
            unit.update_status()

    def change_morale(self, change: float) -> None:
        for unit in self.deployed_units:
            if not unit.pursuing:
                unit.change_morale(change)

    def remove_unit(self, unit: Unit) -> None:
        file = None
        for key, value in self.file_units.items():
            if value is unit:
                file = key
                break

        assert file is not None, "Cannot remove a unit that was not already on a file"
        del self.file_units[file]
        self.removed.append(unit)
        self.deploy_reserve_to_file(file, unit.position)

    def deploy_reserve_to_file(self, file: int, ref_pos: float) -> None:
        if self.reserves:
            new_unit = self.reserves.pop(0)
            new_unit.file = file
            depl_pos = self.position_to_deplot_reserve_at(ref_pos)
            new_unit.position = depl_pos
            self.other_army.move_unit_safely_away_from_pos(file, depl_pos)
            self.file_units[file] = new_unit 

    def position_to_deplot_reserve_at(self, ref_pos: float) -> float:
        # Give some breathing room to reserve units when deployed
        if self.init_position < 0:
            return max(ref_pos - RESERVE_DIST_BEHIND, self.init_position + MIN_RESERVE_DIST)
        else:
            return min(ref_pos + RESERVE_DIST_BEHIND, self.init_position - MIN_RESERVE_DIST)

    def move_unit_safely_away_from_pos(self, file: int, ref_pos: float) -> None:
        # Prevents overlapping units, jumps towards home as necessary
        if file in self.file_units:
            unit = self.file_units[file]

            if unit.position < ref_pos + 1 and self.init_position > 0:
                unit.move_to(ref_pos + 1)
            elif unit.position > ref_pos - 1 and self.init_position < 0:
                unit.move_to(ref_pos - 1)

    # Query
    def unit_blocking_file(self, file: int, ref_pos: float) -> Unit | None:
        """Which unit would an enemy at (file, ref_pos) first encounter, if any"""
        ordered_units: list[tuple[float, int, Unit]] = []  # Middle element is to break ties

        if self.is_file_active(file - 1):
            unit = self.file_units[file - 1]
            ordered_units += [(abs(unit.position-ref_pos) + SIDE_RANGE_PENALTY, 1, unit)]
        
        if self.is_file_active(file + 1):
            unit = self.file_units[file + 1]
            ordered_units += [(abs(unit.position-ref_pos) + SIDE_RANGE_PENALTY, 2, unit)]

        if self.is_file_active(file):
            unit = self.file_units[file]
            ordered_units += [(abs(unit.position-ref_pos), 0, unit)]

        if ordered_units:
            return min(ordered_units)[-1]
        else:
            return None

    def file_state(self, file: int, ref_pos: float) -> int:
        """Who has units in that file and, if both, who is closer to the reference position"""
        self_pre = self.is_file_active(file)
        enem_pre = self.other_army.is_file_active(file)

        if self_pre and not enem_pre:
            return FILE_SUPPORTED

        elif not self_pre and enem_pre:
            return FILE_VULNERABLE

        elif not self_pre and not enem_pre:
            return FILE_EMPTY

        else:  # Both have a unit there
            self_dist = abs(self.file_units[file].position - ref_pos)
            enem_dist = abs(self.other_army.file_units[file].position - ref_pos)

            if self_dist > 1.0 and enem_dist < self_dist:
                return FILE_VULNERABLE
            else:
                return FILE_SUPPORTED

    def is_file_active(self, file: int) -> bool:
        return file in self.file_units


@define(eq=False)
class Fight:
    """A and B both in range and attacking each other"""

    unit_A: Unit
    unit_B: Unit

    balance: float = field(init=False)

    def do(self) -> None:
        self.set_balance()
        self.do_casualties_on_A()
        self.do_casualties_on_B()
        self.do_push()

    def set_balance(self) -> None:
        self.balance = 2.0 ** ((self.unit_A.eff_power() - self.unit_B.eff_power())/(2*POWER_SCALE))

    def do_casualties_on_A(self) -> None:
        self.unit_A.change_morale(- DELTA_T * (1 - self.unit_A.terrain.cover) / self.balance)

    def do_casualties_on_B(self) -> None:
        self.unit_B.change_morale(- DELTA_T * (1 - self.unit_B.terrain.cover) * self.balance)

    def do_push(self) -> None:
        if self.balance >= 1:  # A is pushing B back
            self.do_push_from_winner(self.unit_A, self.unit_B, self.balance)
        else:                  # B is pusing A back
            self.do_push_from_winner(self.unit_B, self.unit_A, 1/self.balance)

    def do_push_from_winner(self, winner: Unit, loser: Unit, balance: float) -> None:
        # Loser runs according to its speed, how badly it lost and rigidity, capped by winners speed
        step = DELTA_T if loser.position < loser.army.init_position else -DELTA_T
        factor = min(1, (balance-1) / (1+loser.rigidity))
        dist = step * min(winner.eff_speed, loser.eff_speed * factor)
        loser.move_by(dist)

        # Used mostly to prevent mutual flanking from pursuing when ahead
        if not winner.is_in_range_of(loser) or not loser.is_in_range_of(winner):
            winner.move_by(dist)


@define(eq=False)
class OneWayFight(Fight):
    """Always A attacking a passive B (whose either flanked or out of range)"""

    def do(self) -> None:
        self.set_balance()
        self.do_casualties_on_B()
        self.unit_B.change_harassment(self.balance)


@define(eq=False)
class FightAssigner:

    army_1: Army
    army_2: Army

    # A unit and all the ones it could attack
    potentials: dict[Unit, set[Unit]] = field(init=False, default=Factory(dict))
    # A unit and the one it is assigned to attack 
    assignments: dict[Unit, Unit] = field(init=False, default=Factory(dict))

    def do(self) -> list[Fight]:
        self.add_all_potentials()
        self.assign_if_unique_target()
        while self.potentials:
            self.assign_best_remaining()
        return self.create_all_fights()

    def add_all_potentials(self) -> None:
        for file, unit in self.army_1.file_units.items():
            self.add_single_potentials(file, unit, self.army_2)

        for file, unit in self.army_2.file_units.items():
            self.add_single_potentials(file, unit, self.army_1)

    def add_single_potentials(self, file: int, unit: Unit, opposing: Army) -> None:
        targets: set[Unit] = set()
        targets |= self.valid_targets(file, unit, opposing)  
        targets |= self.valid_targets(file - 1, unit, opposing)  
        targets |= self.valid_targets(file + 1, unit, opposing)        

        if targets:
            self.potentials[unit] = targets

    def valid_targets(self, file: int, unit: Unit, opposing: Army) -> set[Unit]:
        if file in opposing.file_units:
            target = opposing.file_units[file]
            if unit.is_in_range_of(target):
                return {target}
        return set()

    def assign_if_unique_target(self) -> None:
        for unit, targets in list(self.potentials.items()):
            if len(targets) == 1:
                self.assignments[unit] = list(targets)[0]
                del self.potentials[unit]

    def assign_best_remaining(self) -> None:
        assigned_to = invert_dictionary(self.assignments)

        def sort_key(unit, target):
            """Lots of trial and error needed to get this behaving sensibly - tread lightly
                (Recall that True > False)"""
            attacker = target in assigned_to.get(unit, set())
            frontal = unit.is_in_front(target)
            return (frontal and unit.distance_to(target.position) <= 1 + EPS,
                    attacker,
                    frontal,
                    target not in self.assignments,
                    -unit.distance_to(target.position),
                    -unit.att_range,
                    abs(unit.file),
                    abs(target.file),
                    unit.file, target.file, unit.position)  # Breaks ties in all cases

        score, unit, target = max((sort_key(att, x), att, x) for att in self.potentials
                                  for x in self.potentials[att])

        self.assignments[unit] = target
        del self.potentials[unit]

    def create_all_fights(self) -> list[Fight]:
        remaining = set(self.assignments)
        two_ways: list[Fight] = []
        one_ways: list[Fight] = []

        while remaining:
            unit_A = list(remaining)[0]
            unit_B = self.assignments[unit_A]
            if unit_A is self.assignments.get(unit_B, None):
                two_ways += [Fight(unit_A, unit_B)]
                remaining.remove(unit_A)
                remaining.remove(unit_B)
            else:
                one_ways += [OneWayFight(unit_A, unit_B)]
                remaining.remove(unit_A)

        return two_ways + one_ways


@define(eq=False)
class Battle:

    army_1: Army
    army_2: Army
    landscape: Landscape

    turns: int = field(init=False, default=0)  # Number of turns started
    # Keeping record is useful for output and drawing
    curr_fights: list[Fight] = field(init=False, default=Factory(list))

    def __attrs_post_init__(self) -> None:
        """Pass refernces down the chain as required"""
        self.army_1.set_up(True, self.landscape, self.army_2)
        self.army_2.set_up(False, self.landscape, self.army_1)

    def do(self, verbosity: int) -> None:
        if verbosity >= 10:
            self.print_turn()

        while self.army_1.active and self.army_2.active:
            self.turns += 1
            self.do_turn(verbosity)

        if verbosity >= 0:
            if verbosity < 100:  # Don't reprint when verbosity is high
                self.print_turn()
            self.print_winner()

    def do_turn(self, verbosity: int) -> None:
        self.do_fights()
        self.do_turn_move()
        self.update_status()
        if verbosity >= 100:
            self.print_turn()

    def do_fights(self) -> None:
        self.curr_fights = FightAssigner(self.army_1, self.army_2).do()
        for fight in self.curr_fights:
            fight.do()

    def do_turn_move(self) -> None:
        for army, file, unit in self.order_move():
            enemy = army.other_army.unit_blocking_file(file, unit.position)
            if not enemy:
                unit.move_towards(army.other_army.init_position)
            elif not unit.is_in_range_of(enemy):
                unit.move_towards_range_of(enemy)

    def order_move(self) -> list[tuple[Army, int, Unit]]:
        """"Return a list of (army, file, unit) in order of which unit should move"""
        complete = [(self.army_1, file, unit) for file, unit in self.army_1.file_units.items()]
        complete += [(self.army_2, file, unit) for file, unit in self.army_2.file_units.items()]

        def sort_key(args):
            """Move melee units in centre first (last two are to break tie)"""
            unit = args[2]
            return (unit.att_range, abs(unit.file), -abs(unit.position), unit.file, unit.position)
        return sorted(complete, key=sort_key)

    def update_status(self) -> None:
        """ Repeat incase a unit moved/push into camp, leading to morale loss and other death"""
        self.army_1.update_status()
        self.army_2.update_status()
        self.army_1.update_status()
        self.remove_locked_speed()

    def remove_locked_speed(self) -> None:
        """Armies move at the speed of their slowest unit until fighting starts and/or close"""
        if self.army_1.locked_speed == self.army_2.locked_speed == inf:
            return

        min_sep = min(unit.position for unit in self.army_2.deployed_units)
        min_sep -= max(unit.position for unit in self.army_1.deployed_units)

        if self.curr_fights or min_sep <= LOCKED_SPEED_DIST:
            self.army_1.locked_speed = inf
            self.army_2.locked_speed = inf

    def determine_winner(self) -> int:
        """0 => both won, 1 => army_1 won, 2 => army_2 won, -1 => both lost """
        if self.army_1.defeated and self.army_2.defeated:
            return -1
        elif self.army_1.defeated and not self.army_2.defeated:
            return 2
        elif not self.army_1.defeated and self.army_2.defeated:
            return 1
        else:
            return 0

    # Verbosity
    def print_turn(self) -> None:
        print(f"\nTurn {self.turns}")
        self.print_fights()
        print(self.army_1)
        print(self.army_2)

    def print_fights(self) -> None:
        order = sorted(self.curr_fights, key=lambda x: (x.unit_A.file, x.unit_B.file))
        if order:
            string = "  "
            for fight in order:
                if fight.unit_A.army == self.army_1:
                    file_1, file_2 = fight.unit_A.file, fight.unit_B.file
                    arrow = "-->"
                else:
                    file_2, file_1 = fight.unit_A.file, fight.unit_B.file
                    arrow = "<--"
                if not isinstance(fight, OneWayFight):
                    arrow = "<->"

                string += f"  {file_1} {arrow} {file_2}  |"
            print(string[:-3])

    def print_winner(self) -> None:
        winner = self.determine_winner()
        print(f"\nTurn {self.turns} ")
        if winner == 0:
            print("BOTH ARMIES WERE PARTIALLY VICTORIOUS")
        elif winner == 1:
            print(f"{self.army_1.name} WAS VICTORIOUS")
        elif winner == 2:
            print(f"{self.army_2.name} WAS VICTORIOUS")
        elif winner == -1:
            print("NEITHER ARMIES HELD THE FIELD")


def invert_dictionary(init: dict) -> dict:
    """ Takes {x1: y1, x2: y2, x3: y2, ...} and returns {y1: {x1}, y2: {x2, x3}, ....} """
    fin = {}
    for key, value in init.items():
        if value not in fin:
            fin[value] = {key}
        else:
            fin[value] |= {key}
    return fin


def capped(l_cap: float, y: float, u_cap: float) -> float:
    return max(l_cap, min(y, u_cap))
