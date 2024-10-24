"""Contains all logic for creating and resolving battles"""

from math import prod
from typing import Any, Iterable

from attrs import define, Factory, field

import Config
from Geography import Landscape
from Globals import RESERVE_DIST_BEHIND, SIDE_RANGE_PENALTY, BASE_SPEED, \
                    POWER_SCALE, LOW_MORALE_POWER, PURSUE_MORALE, \
                    FILE_EMPTY, FILE_SUPPORTED, FILE_VULNERABLE, Stance, BattleOutcome
from Unit import Army, Unit


@define(eq=False)
class FightPairs:
    """Decides which units will attack which other units and stores this as lists of tuples"""
    army_1: Army
    army_2: Army
    _potentials: dict[Unit, set[Unit]] = field(init=False, default=Factory(dict))
    _assignments: dict[Unit, Unit] = field(init=False, default=Factory(dict))
    two_way_pairs: list[tuple[Unit, Unit]] = field(init=False, default=Factory(list))
    one_way_pairs: list[tuple[Unit, Unit]] = field(init=False, default=Factory(list))
    all_engaged: set[Unit] = field(init=False, default=Factory(set))

    def reset(self) -> None:
        self._potentials = {}
        self._assignments = {}
        self.two_way_pairs = []
        self.one_way_pairs = []
        self.all_engaged = set()

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
            dist = unit.get_dist_to(target.position)
            melee = (dist <= 1+Unit.EPS) if frontal else (dist <= 1 - SIDE_RANGE_PENALTY+Unit.EPS)
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
            self.all_engaged |= {unit_A, unit_B}


@define(eq=False)
class Battle:
    """Top level class that holds references to everything"""

    # Class attributes, computed from Globals but unchanging
    FILE_MEAN = 0.5 * (FILE_SUPPORTED+FILE_VULNERABLE)
    FILE_DIFF = FILE_SUPPORTED - FILE_VULNERABLE

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

    #############
    """ UTILS """
    #############

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

    def reset_unit_stance(self, unit: Unit) -> None:
        unit.stance = self.get_army_deployed_in(unit).stance

    def call_neighbors_forward(self, unit: Unit) -> None:
        """Make sure neighbors don't stay completely passive and join in if they can"""
        for neighbor in self.get_army_deployed_in(unit).get_neighbors(unit.file, False):
            if neighbor not in self.fight_pairs.all_engaged:
                if neighbor.speed >= unit.speed:  # No point calling slower neighbors as backup
                    neighbor.stance = min(neighbor.stance, Stance.NEUT)

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
        if all(unit.halted for unit in self.iter_all_deployed()):
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
        # Order important, need to change morale before changing files before marking as pursuing
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
            self.reset_unit_stance(unit)

            if self.get_eff_morale(unit) <= 0 or unit.at_home:
                army = self.get_army_deployed_in(unit)
                army.remove_unit(unit, self.get_other_army(army))

            elif unit.at_end and self.get_eff_morale(unit) > 0:
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
        balance = self.compute_fight_balance(unit_A, unit_B)
        self.inflict_casualties(unit_A, 1/balance)
        self.inflict_casualties(unit_B, balance)
        self.push_from_fight(unit_A, unit_B, balance)

    def fight_one_way(self, unit_A: Unit, unit_B: Unit) -> None:
        balance = self.compute_fight_balance(unit_A, unit_B)
        self.inflict_casualties(unit_B, balance)

        unit_B.stance = Stance.AGGR
        self.call_neighbors_forward(unit_B)

    def compute_fight_balance(self, unit_A: Unit, unit_B: Unit) -> float:
        power_dif = self.get_eff_power(unit_A) - self.get_eff_power(unit_B)
        return 2.0 ** (power_dif / (2*POWER_SCALE))

    def get_eff_power(self, unit: Unit) -> float:
        power = unit.power
        power += unit.get_power_from_terrain(self.landscape)
        power += self.get_army_deployed_in(unit).reserve_power
        power += self.get_unit_power_from_morale(unit)
        return power

    def get_unit_power_from_morale(self, unit: Unit) -> float:
        return -LOW_MORALE_POWER * (1 - (self.get_eff_morale(unit) ** (1+unit.rigidity)))

    def get_eff_morale(self, unit: Unit) -> float:
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
        morale = self._morale_from_mean_clash_distance(mean_dist)
        return morale if army.is_file_active(file) else min(0, morale)

    def _morale_from_mean_clash_distance(self, mean_dist: float) -> float:
        if mean_dist > 0.5:
            return FILE_SUPPORTED
        elif mean_dist < -0.5:
            return FILE_VULNERABLE
        else:
            return self.FILE_MEAN + mean_dist*self.FILE_DIFF

    def inflict_casualties(self, unit: Unit, balance: float) -> None:
        cover = 1 - self.landscape.get_mean_cover(unit.file, unit.position)
        unit.morale -= Config.DELTA_T * cover * balance

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
        dist *= BASE_SPEED * Config.DELTA_T * (1 if winner.moving_to_pos else -1)
        loser.move_by(dist)

        # Winner chases only if it keeps fiht active
        if not winner.is_in_range_of(loser) or not loser.is_in_range_of(winner):
            winner.move_by(dist)

    ##############
    """ MOVING """
    ##############

    def move(self) -> None:
        for unit in self.get_move_order():

            army = self.get_army_deployed_in(unit)
            enemy = self.get_other_army(army).get_blocking_unit(unit)

            if not enemy:
                speed = unit.get_eff_speed(self.landscape)
                unit.move_towards(-unit.init_pos, speed)

            elif not unit.is_in_range_of(enemy):
                target = unit.get_position_to_attack_target(enemy)
                self.move_unit_towards_in_stance(unit, target)

    def get_move_order(self) -> list[Unit]:
        """Move melee units in centre first (last two are to break tie)"""
        return sorted(self.iter_all_deployed(), key=lambda x:
                      (x.stance.value, -x.speed, x.att_range, abs(x.file), -abs(x.position),
                       x.file, x.position))

    def move_unit_towards_in_stance(self, unit: Unit, target: float) -> None:
        quick = unit.get_eff_speed(self.landscape) 
        slow = self.get_army_deployed_in(unit).get_cohesive_speed(unit, target, self.landscape)

        if unit.stance is Stance.AGGR:
            unit.move_towards(target, quick)
        elif unit.stance is Stance.NEUT:
            unit.move_towards(target, quick if unit.is_charge_range_of(target) else slow)
        elif unit.stance is Stance.DEFN:
            self.move_towards_haltingly(unit, target, slow)
        else:
            raise ValueError(f"Unknown stance {unit.stance}")

    def move_towards_haltingly(self, unit: Unit, target: float, speed: float) -> None:
        """Confirm movement only if it does not reduce desire or increase distance from supporting
        units on the flanks too much"""
        army = self.get_army_deployed_in(unit)
        backwards_unit = army.get_backwards_neighbor(unit)

        old_pos = unit.position
        old_desire = self.get_unit_pos_desire(unit)
        old_lag = unit.get_dist_to(backwards_unit.position) if backwards_unit else 0

        unit.move_towards(target, speed)
        new_desire = self.get_unit_pos_desire(unit)
        new_lag = unit.get_dist_to(backwards_unit.position) if backwards_unit else 0

        # Gradient of power change, reduced if neighbors are engaged
        power_grad = (old_desire - new_desire) / unit.get_dist_to(old_pos)
        power_grad *= prod((0.5 for neighbor in army.get_neighbors(unit.file)
                           if neighbor in self.fight_pairs.all_engaged))

        unit.confirm_move(power_grad, old_pos, old_lag, new_lag)

    def get_unit_pos_desire(self, unit: Unit) -> float:
        cover = self.landscape.get_mean_cover(unit.file, unit.position)
        return self.get_eff_power(unit) + 10*cover 

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
        print(self.army_1.str_in_battle(self.landscape, self.get_eff_power, self.get_eff_morale))
        print(self.army_2.str_in_battle(self.landscape, self.get_eff_power, self.get_eff_morale))

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
    output: dict[Any, Any] = {}
    for key, value in init.items():
        output[value] = output[value] | {key} if (value in output) else {key}
    return output
