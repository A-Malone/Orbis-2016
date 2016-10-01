from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *


class Agent:
    def __init__(self):
        self.objectives = []

    def update(self, friendly):
        self.assigned_move = None

        self.unit = friendly
        # Inherit from friendly
        self.position = friendly.position
        self.team = friendly.team
        self.call_sign = friendly.call_sign
        self.current_weapon_type = friendly.current_weapon_type

    def do_move(self, world, enemy_units, friendly_units):
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

        # Move to pick ups
        for pickup in sorted(world.pickups,
                             key=lambda p: world.get_path_length(self.position, p.position)):
            if self.check_move_to_destination(
                    pickup.position) == MoveResult.MOVE_VALID:
                self.move_to_destination(pickup.position)
                return

        # Move to enemy mainframe
        for enemy_mainframe in sorted(
                filter(lambda c: c.is_mainframe and c.controlling_team != self.team, world.control_points),
                key=lambda p: world.get_path_length(self.position, p.position)):
            if self.check_move_to_destination(
                    enemy_mainframe.position) == MoveResult.MOVE_VALID:
                self.move_to_destination(enemy_mainframe.position)
                return

        # Move to enemies
        for enemy in sorted(enemy_units, key=lambda e: world.get_path_length(self.position, e.position)):
            if self.check_move_to_destination(
                    enemy.position) == MoveResult.MOVE_VALID:
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
        # I inlined the actual implementation of Entity.move_to_destination to make it call our version
        return self.move(self.unit._world.get_next_direction_in_path(self.unit.position, destination))

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