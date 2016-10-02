from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
from astar import AStar
from objectives import *


class Agent:
    def __init__(self):
        self.objectives = []

    def update(self, friendly, damage_map):
        self.assigned_move = None

        self.unit = friendly
        # Inherit from friendly
        self.position = friendly.position
        self.team = friendly.team
        self.call_sign = friendly.call_sign
        self.current_weapon_type = friendly.current_weapon_type

        self.damage_map = damage_map

    def update_objectives(self):
        if not self.objectives:
            return

        # Remove complete objectives
        self.objectives = [o for o in self.objectives if not o.complete]

    def do_objectives(self, world, enemy_units, friendly_units):
        # Shoot if someone is in range
        for enemy in enemy_units:
            shot_prediction = self.check_shot_against_enemy(enemy)
            if shot_prediction == ShotResult.CAN_HIT_ENEMY:
                self.shoot_at(enemy)
                return

        # Pick up what you're standing on
        if self.check_pickup_result() == PickupResult.PICK_UP_VALID:
            self.pickup_item_at_position()
            return

        if not self.objectives:
            return

        # Work on the current objective
        o = self.objectives[-1]
        if (isinstance(o, AttackCapturePointObjective)):
            self.move_to_destination(o.position)

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
            raise "ERROR"
        move_target = path.path_list[-1]
        # self.damage_map.reserve_position(move_target)
        return self.unit.move_to_destination(move_target)

    def pickup_item_at_position(self):
        if self.assigned_move is not None:
            raise "Assigned move to unit with move already!"
        self.assigned_move = "PICKUP"
        return self.unit.pickup_item_at_position()

    def shoot_at(self, enemy_unit):
        if self.assigned_move is not None:
            raise "Assigned move to unit with move already!"
        self.assigned_move = "SHOOT " + str(enemy_unit)
        return self.unit.shoot_at(enemy_unit)

    def standby(self):
        if self.assigned_move is not None:
            raise "Assigned move to unit with move already!"
        self.assigned_move = "STANDBY"
        return self.unit.standby()
