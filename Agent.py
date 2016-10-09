from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
from astar import AStar
from DamageCounter import DamageCounter
from objectives import *
import Utils
import traceback


class Agent:
    def __init__(self):
        self.objective_max_priority = 0
        self.objectives = []        

    def update(self, friendly, enemy_units, damage_map, enemy_damage_counter_prediction):        
        self.assigned_move = None

        # Sketchy superclassing!
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
            shot_prediction = self.unit.check_shot_against_enemy(enemy)
            if shot_prediction == ShotResult.CAN_HIT_ENEMY and enemy.shielded_turns_remaining <= 0:
                self.enemy_damage_counter_prediction[enemy.call_sign].add_damage(self)
        

    def update_objectives(self):
        if not self.objectives:
            return

        # Remove complete objectives
        self.objectives = [o for o in self.objectives if not o.complete]
        

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
            if self.unit.get_last_turn_shooters() and self.unit.check_shield_activation() == ActivateShieldResult.SHIELD_ACTIVATION_VALID:
                self.activate_shield()
                return

            # Work on the current objective
            if len(self.objectives) > 0:
                o = self.objectives[-1]
                if (isinstance(o, AttackCapturePointObjective) or isinstance(o, DefendCapturePointObjective)):
                    self.move_to_destination(o.position)
                    return
                elif isinstance(o, PickupObjective):
                    if self.position == o.position and self.unit.check_pickup_result() == PickupResult.PICK_UP_VALID:
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
        except ValueError:
            traceback.print_exc()

    def objective_cost(self, world, objective):
        
        if(not self.objectives):
            return (0,0)
        
        best_cost = Utils.path_cost(world, self.position, objective.position, self.objectives[-1].position, self.objectives[0].position)
        best_index = len(self.objectives)

        for i in range(0,len(self.objectives)-1,):
            cost = Utils.path_cost(world, self.objectives[i+1].position, objective.position, self.objectives[i].position, self.objectives[0].position)            
            if (cost < best_cost):
                best_cost = cost
                best_index = i+1

        return (best_cost, best_index)

    def has_no_assigned_move(self):
        return self.assigned_move is None

    def activate_shield(self):
        if self.assigned_move is not None:
            raise ValueError("Assigned move to unit with move already!")
        self.assigned_move = "SHIELD"
        return self.unit.activate_shield()

    def move_to_destination(self, destination):
        # Custom A* implementation
        astar = AStar()
        if self.unit.last_move_result in [MoveResult.BLOCKED_BY_ENEMY, MoveResult.BLOCKED_BY_FRIENDLY,
                                     MoveResult.BLOCKED_BY_WORLD]:
            astar.closed_set.add(self.last_move_destination)
        path = astar.get_path(self, self.position, destination, self.damage_map)
        if not path or len(path.path_list) == 0:
            # COULD NOT FIND PATH
            traceback.print_exc()
            return
        move_target = path.path_list[-1]
        # self.damage_map.reserve_position(move_target)
        self.assigned_move = "MOVE " + str(move_target)
        self.last_move_destination = move_target
        return self.unit.move_to_destination(move_target)

    def pickup_item_at_position(self):
        if self.assigned_move is not None:
            raise ValueError("Assigned move to unit with move already!")
        self.assigned_move = "PICKUP"
        return self.unit.pickup_item_at_position()

    def shoot_at(self, enemy_unit):
        """
        :param EnemyUnit enemy_unit:
        """
        if self.assigned_move is not None:
            raise ValueError("Assigned move to unit with move already!")
        self.assigned_move = "SHOOT " + str(enemy_unit)
        return self.unit.shoot_at(enemy_unit)

    def standby(self):
        if self.assigned_move is not None:
            raise ValueError("Assigned move to unit with move already!")
        self.assigned_move = "STANDBY"
        return self.unit.standby()

    def needs_weapon(self):
        return self.current_weapon_type == WeaponType.MINI_BLASTER and not any(filter(lambda o : is_weapon_objective(o), self.objectives))
