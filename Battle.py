"""Contains all logic for creating and resolving battles"""
from itertools import chain
from typing import Any, Iterable

from attrs import define, Factory, field

from Config import DELTA_T
from Geography import Landscape
from Globals import RESERVE_DIST_BEHIND, BASE_SPEED, PUSH_RESISTANCE, HALT_POWER_GRADIENT, \
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

    def reset(self) -> None:
        self._potentials = {}
        self._assignments = {}
        self.two_way_pairs = []
        self.one_way_pairs = []

    ##################
    """ ASSIGNMENT """
    ##################

    def assign_all(self) -> None:
        self.reset()
        self.add_all_potentials()
        while self._potentials:
            self.assign_best_remaining()

    def add_all_potentials(self) -> None:
        for file, unit in self.army_1.file_units.items():
            self.add_single_potentials(file, unit, self.army_2)

        for file, unit in self.army_2.file_units.items():
            self.add_single_potentials(file, unit, self.army_1)

    def add_single_potentials(self, file: int, unit: Unit, opposing: Army) -> None:
        targets = self.find_single_potentials(file, unit, opposing)
        if not targets:
            return
        elif len(targets) == 1:
            self.match_into_pair(unit, targets.pop())
        else:
            self._potentials[unit] = targets

    def find_single_potentials(self, file: int, unit: Unit, opposing: Army) -> set[Unit]:
        targets: set[Unit] = set()

        # TODO: TEST
        files = opposing.file_units.keys() if unit.all_sides else [file-1, file, file+1]
        for file in files:
            target = opposing.file_units.get(file, None)
            if target is not None and unit.is_in_range_of(target):
                targets.add(target)

        return targets

    def assign_best_remaining(self) -> None:
        assigned_to = invert_dictionary(self._assignments)

        def sort_key(args: tuple[Unit, Unit]):
            """Lots of trial and error needed to get this behaving sensibly - tread lightly
                (Recall that True > False)"""
            unit, target = args
            frontal = unit.is_in_front(target)
            dist = unit.get_dist_to(target.position) + unit.get_range_penalty_against(target)  # TODO: TEST
            melee = unit.is_in_range_of(target, melee=True)
            attacker = target in assigned_to.get(unit, set())
            unassigned = target not in self._assignments
            return (frontal and melee,                                         # Always do if true
                    melee, frontal, attacker, unassigned,                      # Top rank priorities
                    -dist, -unit.att_range, abs(unit.file), abs(target.file),  # Remaing priorities
                    unit.file, target.file, unit.position)                     # Breaks any ties

        unit, target = max(((unit, target)
                           for unit in self._potentials for target in self._potentials[unit]),
                           key=sort_key)
        del self._potentials[unit]
        self.match_into_pair(unit, target)

    def match_into_pair(self, unit: Unit, target: Unit) -> None:
        self._assignments[unit] = target
        if (target, unit) in self.one_way_pairs:
            self.one_way_pairs.remove((target, unit))
            self.two_way_pairs.append((unit, target))
        else:
            self.one_way_pairs.append((unit, target))

    ###############
    """ QUERIES """
    ###############

    def is_attacking(self, unit: Unit) -> bool:
        return unit in self._assignments

    def is_not_attacking_except_target(self, unit: Unit, enemy: Unit) -> bool:
        if unit in self._assignments and self._assignments[unit] is not enemy:
            return False
        return True


@define(eq=False)
class Battle:
    """Top level class that holds references to everything"""

    # Class attributes, computed from Globals but unchanging
    FILE_MEAN = 0.5 * (FILE_SUPPORTED+FILE_VULNERABLE)
    FILE_DIFF = FILE_SUPPORTED - FILE_VULNERABLE
    FILE_WEIGHT = RESERVE_DIST_BEHIND - 0.5

    army_1: Army
    army_2: Army
    landscape: Landscape
    fight_pairs: FightPairs = field(init=False)
    turns: int = field(init=False, default=0)

    @fight_pairs.default
    def _default_fight_pairs(self) -> FightPairs: return FightPairs(self.army_1, self.army_2)

    def __attrs_post_init__(self) -> None:
        """Armies positioned symmetrically, with the total gap being the sum of their reach"""
        init_pos = (self.army_1.army_reach + self.army_2.army_reach) / 2
        self.army_1.set_up(-init_pos, self.landscape)
        self.army_2.set_up(init_pos, self.landscape)

    #############
    """ UTILS """
    #############

    def iter_all_deployed(self) -> Iterable[Unit]:
        return chain(self.army_1.deployed_units, self.army_2.deployed_units)

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

    def is_battle_ended(self) -> bool:
        if self.army_1.defeated or self.army_2.defeated:
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
        units_to_remove: list[Unit] = []

        for unit in sorted(self.iter_all_deployed(), key=lambda x: abs(x.file)):
            if self.do_unit_tidy_to_remove(unit):
                units_to_remove.append(unit)

        self.remove_units(units_to_remove)

    def do_unit_tidy_to_remove(self, unit: Unit) -> bool:
        self.reset_unit_stance(unit)
        unit.forced_move_towards = None
        if unit.at_end:
            self.do_unit_reached_end(unit)
        return self.get_eff_morale(unit) <= 0 or unit.at_home

    def do_unit_reached_end(self, unit: Unit) -> None:
        army = self.get_army_deployed_in(unit)
        other_army = self.get_other_army(army)

        other_army.change_all_units_morale(PURSUE_MORALE * DELTA_T)

        if unit.file != 0 and other_army.get_blocking_unit(unit) is None:
            if not army.is_file_towards_centre_active(unit.file):
                army.slide_file_towards_centre(unit.file)            

    def remove_units(self, units_to_remove: Iterable[Unit]) -> None:
        for unit in units_to_remove:
            army = self.get_army_deployed_in(unit)
            army.remove_unit(unit, self.get_other_army(army))             

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
        adv_A = self.compute_fight_advantage(unit_A, unit_B)
        adv_B = self.compute_fight_advantage(unit_B, unit_A)
        self.inflict_casualties(unit_A, adv_B)
        self.inflict_casualties(unit_B, adv_A)
        self.move_post_fight_two_way(unit_A, unit_B, adv_A, adv_B)

    def fight_one_way(self, unit_A: Unit, unit_B: Unit) -> None:
        advantage = self.compute_fight_advantage(unit_A, unit_B)
        self.inflict_casualties(unit_B, advantage)
        self.move_post_fight_one_way(unit_A, unit_B)

    def compute_fight_advantage(self, attacker: Unit, defender: Unit) -> float:
        if attacker.is_in_range_of(defender, melee=True):
            att_pow = attacker.power
            def_power = defender.power
        else:
            att_pow = attacker.pow_range
            def_power = max(defender.power, defender.pow_range)

        att_pow += self.get_power_mods(attacker)
        def_power += self.get_power_mods(defender)

        return 2.0 ** ((att_pow - def_power) / (2*POWER_SCALE))

    def get_power_mods(self, unit: Unit) -> float:
        change = unit.power_from_terrain
        change += self.get_army_deployed_in(unit).reserve_power
        change += self.get_unit_power_from_morale(unit)
        return change

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

        own_dist = -RESERVE_DIST_BEHIND  # If not friendly, assume fictional unit this far behind
        if army.is_file_active(file):
            own_dist = max(own_dist, unit.get_signed_distance_to_unit(army.file_units[file]))

        """Mean is weighted towards the enemy: friendly units protect further than enemies threaten.
        Matches RESERVE_DIST_BEHIND such that flanking melee range just causes full vulnerablity
        when there are no supporting units"""
        mean_dist = (self.FILE_WEIGHT*ene_dist + own_dist) / (1 + self.FILE_WEIGHT)
        morale = self._morale_from_mean_clash_distance(mean_dist)
        return morale if army.is_file_active(file) else min(0, morale)

    def _morale_from_mean_clash_distance(self, mean_dist: float) -> float:
        if mean_dist > 0.5:
            return FILE_SUPPORTED
        elif mean_dist < -0.5:
            return FILE_VULNERABLE
        else:
            return self.FILE_MEAN + mean_dist*self.FILE_DIFF

    def inflict_casualties(self, unit: Unit, adv: float) -> None:
        unit.morale -= DELTA_T * adv * (1-unit.cover_from_terrain)

    def move_post_fight_two_way(self, unit_A: Unit, unit_B: Unit, advA: float, advB: float) -> None:
        self.call_neighbors_forwards(unit_A, unit_B)
        self.call_neighbors_forwards(unit_B, unit_A)
        self.set_force_move_two_way_fight(unit_A, unit_B)
        self.do_push(unit_A, unit_B, advA, advB)

    def move_post_fight_one_way(self, unit_A: Unit, unit_B: Unit) -> None:
        self.call_neighbors_forwards(unit_B, unit_A)
        if not self.fight_pairs.is_attacking(unit_B):
            # Do not change stance if already fighting elsewhere
            unit_B.stance = Stance.AGG
        self.set_force_move_one_way_fight(unit_A, unit_B)

    def call_neighbors_forwards(self, unit: Unit, enemy: Unit) -> None:
        """Neighbors that are: not attacking someone else & can hit the attacker quickly, join in"""
        for neighbor in self.get_army_deployed_in(unit).get_neighbors(unit.file, False):
            if self.fight_pairs.is_not_attacking_except_target(neighbor, enemy):
                if neighbor.get_dist_to(enemy.position) <= neighbor.att_range + neighbor.speed:
                    neighbor.stance = min(neighbor.stance, Stance.BAL)

    def set_force_move_two_way_fight(self, unit_A: Unit, unit_B: Unit) -> None:
        """Which unit, if any, will advance towards enemy currently engaged with"""
        if unit_A.is_in_range_of(unit_B, melee=True):
            pass
        elif unit_A.ranged and unit_B.ranged:
            pass
        elif unit_A.ranged and unit_B.mixed and (unit_B.stance is not Stance.DEF):
            unit_B.forced_move_towards = unit_A
        elif unit_A.mixed and unit_B.ranged and (unit_A.stance is not Stance.DEF):
            unit_A.forced_move_towards = unit_B

        elif unit_A.mixed and unit_B.mixed:
            if not unit_A.is_in_front(unit_B):
                unit_A.forced_move_towards = unit_B
                unit_B.forced_move_towards = unit_A
            if unit_A.stance is Stance.AGG:
                unit_A.forced_move_towards = unit_B
            if unit_B.stance is Stance.AGG:
                unit_B.forced_move_towards = unit_A

    def set_force_move_one_way_fight(self, unit_A: Unit, unit_B: Unit) -> None:
        if unit_A.mixed and not unit_A.is_in_range_of(unit_B, melee=True):
            if unit_A.stance is Stance.AGG:
                unit_A.forced_move_towards = unit_B
            elif unit_A.stance is Stance.BAL and unit_B.ranged:
                unit_A.forced_move_towards = unit_B
            elif unit_A.stance is Stance.BAL and unit_B.mixed and not unit_A.is_in_front(unit_B):
                unit_A.forced_move_towards = unit_B

    def do_push(self, unit_A: Unit, unit_B: Unit, adv_A: float, adv_B: float) -> None:
        if unit_A.forced_move_towards is None and unit_B.forced_move_towards is None:
            if adv_A > adv_B and adv_A > 1:
                self._loser_push_by_winner(unit_A, unit_B, adv_A)
            elif adv_A < adv_B and adv_B > 1:
                self._loser_push_by_winner(unit_B, unit_A, adv_B)

    def _loser_push_by_winner(self, winner: Unit, loser: Unit, advantage: float) -> None:
        # Loser runs according to its speed, how badly it lost and rigidity, capped by winners speed
        coef = min(1, (advantage - 1) / (PUSH_RESISTANCE + loser.rigidity))
        dist = min(winner.eff_speed, loser.eff_speed * coef)
        dist *= BASE_SPEED * DELTA_T * (1 if winner.moving_to_pos else -1)
        loser.position += dist
        self._follow_push_by_winner(winner, loser, dist)

    def _follow_push_by_winner(self, winner: Unit, loser: Unit, dist: float) -> None:
        """Follow only to stay in range (melee range for non-defensive mixed units)"""
        winner_force_melee = winner.mixed and winner.stance is not Stance.DEF
        winner_in_range = winner.is_in_range_of(loser, melee=winner_force_melee)

        loser_force_melee = loser.mixed and loser.stance is not Stance.DEF
        loser_in_range = loser.is_in_range_of(winner, melee=loser_force_melee)

        if not winner_in_range or not loser_in_range:
            winner.position += dist

    ##############
    """ MOVING """
    ##############

    def move(self) -> None:
        for unit in self.get_move_order():
            if unit.forced_move_towards:
                target = unit.get_position_to_attack_target(unit.forced_move_towards, True)
                self.move_unit_in_stance(unit, target)

            else:
                army = self.get_army_deployed_in(unit)
                enemy = self.get_other_army(army).get_blocking_unit(unit)
                if not enemy:
                    unit.move_towards(-unit.init_pos, unit.eff_speed)
                elif not unit.is_in_range_of(enemy):
                    target = unit.get_position_to_attack_target(enemy, False)
                    self.move_unit_in_stance(unit, target)

    def get_move_order(self) -> list[Unit]:
        """Move melee units in centre first (last two are to break tie)"""
        return sorted(self.iter_all_deployed(), key=lambda x:
                      (x.stance.value, -x.speed, x.att_range, abs(x.file), -abs(x.position),
                       x.file, x.position))

    def move_unit_in_stance(self, unit: Unit, target: float) -> None:
        army = self.get_army_deployed_in(unit)

        if unit.stance is Stance.AGG:
            if unit.is_in_charge_range_of(target):
                speed = unit.eff_speed
            else:
                speed = army.get_aggressive_speed(unit, target)
            unit.move_towards(target, speed)

        elif unit.stance is Stance.BAL:
            if unit.is_in_charge_range_of(target):
                speed = unit.eff_speed
            else:
                speed = army.get_cohesive_speed(unit, target)
            unit.move_towards(target, speed)

        elif unit.stance is Stance.DEF:
            speed = army.get_cohesive_speed(unit, target)
            self.move_unit_haltingly(unit, target, speed)

        else:
            raise ValueError(f"Unknown stance {unit.stance}")

    def move_unit_haltingly(self, unit: Unit, target: float, speed: float) -> None:
        """Confirm movement only if it does not reduce desire or increase distance from supporting
        units on the flanks too much"""
        backwards_unit = self.get_army_deployed_in(unit).get_backwards_neighbor(unit)

        old_pos = unit.position
        old_desire = self.get_unit_pos_desire(unit)
        old_lag = unit.get_dist_to(backwards_unit.position) if backwards_unit else 0

        unit.move_towards(target, speed)
        if unit.position == old_pos:
            return  # Prevents later division by 0 and, if not moving anyway, rest is pointless

        new_lag = unit.get_dist_to(backwards_unit.position) if backwards_unit else 0
        gradient = (old_desire - self.get_unit_pos_desire(unit)) / unit.get_dist_to(old_pos)
        gradient += (0.5 - abs(unit.position)/abs(unit.init_pos)) * HALT_POWER_GRADIENT
        # Adds a desire of +-1/2 of required to stop in the middle of battlefield rather than edge

        unit.confirm_move(gradient, old_pos, old_lag, new_lag)

    def get_unit_pos_desire(self, unit: Unit) -> float:
        return self.get_power_mods(unit) + 10*unit.cover_from_terrain

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
        for army in (self.army_1, self.army_2):
            print(army.str_in_battle(self.get_power_mods, self.get_eff_morale))

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
