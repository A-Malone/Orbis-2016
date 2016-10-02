from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
from astar import AStar
from DamageCounter import DamageCounter
from objectives import *
import traceback


class Agent:
    def __init__(self):
        self.objectives = []
        self.needs_weapon = True

    def update(self, friendly, enemy_units, damage_map, enemy_damage_counter_prediction):
        try:
            self.assigned_move = None

            self.unit = friendly
            # Inherit from friendly
            self.position = friendly.position
            self.team = friendly.team
            self.call_sign = friendly.call_sign
            self.current_weapon_type = friendly.current_weapon_type
            self.health = friendly.health
            self.last_move_result = friendly.last_move_result
            self.last_shot_result = friendly.last_shot_result
            self.last_pickup_result = friendly.last_pickup_result
            self.last_shield_activation_result = friendly.last_shield_activation_result
            self.damage_taken_last_turn = friendly.damage_taken_last_turn

            self.damage_map = damage_map
            self.enemy_damage_counter_prediction = enemy_damage_counter_prediction

            # Prepare to shoot if someone is in range, prioritizing low hp
            for enemy in enemy_units:
                shot_prediction = self.check_shot_against_enemy(enemy)
                if shot_prediction == ShotResult.CAN_HIT_ENEMY and enemy.shielded_turns_remaining <= 0:
                    self.enemy_damage_counter_prediction[enemy.call_sign].add_damage(self)
        except e:
            traceback.print_exc()

    def update_objectives(self):
        try:
            if not self.objectives:
                return

            # Remove complete objectives
            self.objectives = [o for o in self.objectives if not o.complete]
        except e:
            traceback.print_exc()

    def do_objectives(self, world, enemy_units, friendly_units):
        try:
            if self.health == 0:
                return

            # Shoot guaranteed kills
            for dc in sorted(filter(lambda v: v.get_total_damage() > v.target.health,
                                    self.enemy_damage_counter_prediction.values()),
                             key=lambda v: len(v.attackers)):
                if self in dc.attackers:
                    self.shoot_at(dc.target)
                    return
            # Shoot anything else in range that's not shielded
            for dc in sorted(
                    filter(lambda v: v.target.shielded_turns_remaining <= 0, self.enemy_damage_counter_prediction.values()),
                    key=lambda v: len(v.attackers),
                    reverse=True):
                if self in dc.attackers:
                    self.shoot_at(dc.target)
                    return

            # Shield
            if self.get_last_turn_shooters() and self.check_shield_activation() == ActivateShieldResult.SHIELD_ACTIVATION_VALID:
                self.activate_shield()
                return

            # Work on the current objective
            if len(self.objectives) > 0:
                o = self.objectives[-1]
                if (isinstance(o, AttackCapturePointObjective)):
                    self.move_to_destination(o.position)
                    return
                elif isinstance(o, PickupObjective):
                    if self.position == o.position and self.check_pickup_result() == PickupResult.PICK_UP_VALID:
                        self.pickup_item_at_position()
                        return
                    else:
                        self.move_to_destination(o.position)
                        return
            else:
                for enemy in sorted(filter(lambda e: e.health != 0, enemy_units),
                                    key=lambda e: world.get_path_length(self.position, e.position)):
                    self.move_to_destination(enemy.position)
                    return
        except e:
            traceback.print_exc()

    def has_no_assigned_move(self):
        return self.assigned_move is None

    def check_move_in_direction(self, direction):
        return self.unit.check_move_in_direction(direction)

    def check_move_to_destination(self, destination):
        return self.unit.check_move_to_destination(destination)

    def check_pickup_result(self):
        return self.unit.check_pickup_result()

    def check_shield_activation(self):
        return self.unit.check_shield_activation()

    def check_shot_against_enemy(self, enemy):
        return self.unit.check_shot_against_enemy(enemy)

    def get_last_turn_shooters(self):
        return self.unit.get_last_turn_shooters()

    def activate_shield(self):
        if self.assigned_move is not None:
            raise "Assigned move to unit with move already!"
        self.assigned_move = "SHIELD"
        return self.unit.activate_shield()

    def move_to_destination(self, destination):
        # Custom A* implementation
        astar = AStar()
        if self.last_move_result in [MoveResult.BLOCKED_BY_ENEMY, MoveResult.BLOCKED_BY_FRIENDLY,
                                     MoveResult.BLOCKED_BY_WORLD]:
            astar.closed_set.add(self.last_move_destination)
        path = astar.get_path(self, self.position, destination, self.damage_map)
        if not path or len(path.path_list) == 0:
            traceback.print_tb()
        move_target = path.path_list[-1]
        # self.damage_map.reserve_position(move_target)
        self.assigned_move = "MOVE " + str(move_target)
        self.last_move_destination = move_target
        return self.unit.move_to_destination(move_target)

    def pickup_item_at_position(self):
        if self.assigned_move is not None:
            raise "Assigned move to unit with move already!"
        self.assigned_move = "PICKUP"
        return self.unit.pickup_item_at_position()

    def shoot_at(self, enemy_unit):
        """
        :param EnemyUnit enemy_unit:
        """
        if self.assigned_move is not None:
            raise "Assigned move to unit with move already!"
        self.assigned_move = "SHOOT " + str(enemy_unit)
        return self.unit.shoot_at(enemy_unit)

    def standby(self):
        if self.assigned_move is not None:
            raise "Assigned move to unit with move already!"
        self.assigned_move = "STANDBY"
        return self.unit.standby()
