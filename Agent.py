from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
from astar import AStar
from DamageCounter import DamageCounter
from objectives import *


class Agent:
    def __init__(self):
        self.objectives = []

    def update(self, friendly, enemy_units, damage_map, enemy_damage_counter_prediction):
        self.assigned_move = None

        self.unit = friendly
        # Inherit from friendly
        self.position = friendly.position
        self.team = friendly.team
        self.call_sign = friendly.call_sign
        self.current_weapon_type = friendly.current_weapon_type
        self.health = friendly.health

        self.damage_map = damage_map
        self.enemy_damage_counter_prediction = enemy_damage_counter_prediction

        # Prepare to shoot if someone is in range, prioritizing low hp
        for enemy in enemy_units:
            shot_prediction = self.check_shot_against_enemy(enemy)
            if shot_prediction == ShotResult.CAN_HIT_ENEMY:
                self.enemy_damage_counter_prediction[enemy.call_sign].add_damage(self)

    def update_objectives(self):
        if not self.objectives:
            return

        # Remove complete objectives
        self.objectives = [o for o in self.objectives if not o.complete]

    def do_objectives(self, world, enemy_units, friendly_units):
        if self.health == 0:
            return

        # Shoot guaranteed kills
        for enemy_callsign, dc in sorted(filter(lambda v: v[1].get_total_damage() > v[1].target.health,
                                                self.enemy_damage_counter_prediction.items()),
                                         key=lambda v: len(v[1].attackers)):
            if self in dc.attackers:
                self.shoot_at(dc.target)
                return

        # Shoot anything else in range
        for enemy_callsign, dc in sorted(self.enemy_damage_counter_prediction.items(),
                                         key=lambda v: len(v[1].attackers),
                                         reverse=True):
            if self in dc.attackers:
                self.shoot_at(dc.target)
                return

        if self.get_last_turn_shooters() and self.check_shield_activation() == ActivateShieldResult.SHIELD_ACTIVATION_VALID:
            self.activate_shield()
            return

        # Pick up what you're standing on
        if self.check_pickup_result() == PickupResult.PICK_UP_VALID:
            self.pickup_item_at_position()
            return

        # Work on the current objective
        if len(self.objectives) > 0:
            o = self.objectives[-1]
            if (isinstance(o, AttackCapturePointObjective)):
                self.move_to_destination(o.position)
        else:
            for enemy in sorted(filter(lambda e: e.health != 0, enemy_units),
                                key=lambda e: world.get_path_length(self.position, e.position)):
                self.move_to_destination(enemy.position)
                return

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

    def move(self, direction):
        if self.assigned_move is not None:
            raise "Assigned move to unit with move already!"
        self.assigned_move = "MOVE " + str(direction)
        return self.unit.move(direction)

    def move_to_destination(self, destination):
        # Custom A* implementation
        astar = AStar()
        path = astar.get_path(self, self.position, destination, self.damage_map)
        if not path or len(path.path_list) == 0:
            print([(x.complete, x.position) for x in self.objectives])
            raise ValueError("Invalid path")
        move_target = path.path_list[-1]
        # self.damage_map.reserve_position(move_target)
        self.assigned_move = "MOVE " + str(move_target)
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
