from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
import itertools
import time

from Agent import Agent
from DamageCounter import DamageCounter
from objectives import *
from damage_map import DamageMap
from astar import AStar

DUMP_OBJECTIVES = False
DUMP_ASSIGNED_MOVES = True


class PlayerAI:
    def __init__(self):
        self.iterations = 0
        self.clearances = []
        self.agents = [Agent() for i in range(4)]
        self.damage_map = DamageMap()

        self.objectives = []
        self.position_to_objective_map = {}

    def do_move(self, world, enemy_units, friendly_units):
        """
        This method will get called every turn; Your glorious AI code goes here.

        :param World world: The latest state of the world.
        :param list[EnemyUnit] enemy_units: An array of all 4 units on the enemy team. Their order won't change.
        :param list[FriendlyUnit] friendly_units: An array of all 4 units on your team. Their order won't change.
        """

        # ---- UPDATES
        # ----------------------------------------
        print("iteration: {}".format(self.iterations))
        if self.iterations == 0:
            self.team = friendly_units[0].team
        # self.clearances = [[0 for x in range(world.width)] for y in range(world.height)]
        #     for x, y in itertools.product(range(world.width), range(world.height)):
        #         tile_type = world.get_tile((x, y));
        #         if tile_type == TileType.WALL:
        #             continue
        #         self.clearances[y][x] = get_max_clearance(world, x, y)
        #     pretty_print_matrix(self.clearances)


        self.damage_map.update_map(world, enemy_units)
        self.update_agents(enemy_units, friendly_units)

        # ---- UPDATE CURRENT OBJECTIVES
        # ----------------------------------------

        # Update objective scores, and perform update logic
        for obj in self.objectives:
            obj.update(world, enemy_units, friendly_units)

        # Filter out complete objectives
        self.objectives = [x for x in self.objectives if not x.complete]

        for agent in self.agents:
            agent.update_objectives()

        # ---- IDENTIFY AND UPDATE NEW OBJECTIVES
        # ----------------------------------------
        # TODO: Add new objectives here

        new_objs = []

        # Control point objectives
        for control_point in world.control_points:
            cp_obj = self.position_to_objective_map.get(control_point.position, None)

            if (not cp_obj or cp_obj.complete == True):
                if (control_point.controlling_team == self.team):
                    new_objs.append(DefendCapturePointObjective(control_point))
                else:
                    new_objs.append(AttackCapturePointObjective(control_point))

        # Update objective scores, and perform update logic
        for obj in new_objs:
            obj.update(world, enemy_units, friendly_units)

        self.objectives += new_objs

        # ---- ORDER AND ASSIGN OBJECTIVES
        # ----------------------------------------

        # Assign objectives to agents
        # For each control point we have that isn't already ours, in order of influence
        for obj in filter(lambda o: isinstance(o, AttackCapturePointObjective), self.objectives):
            for agent in sorted(filter(lambda a: len(a.objectives) == 0, self.agents),
                                key=lambda a: world.get_path_length(a.position, obj.position)):
                agent.objectives.append(obj)
                break

        # ---- DO OBJECTIVES
        # ----------------------------------------

        # Agents do what they have been assigned
        enemy_damage_counter = [0 for i in enemy_units]
        for agent in self.agents:
            agent.do_objectives(world, enemy_units, friendly_units)
            if DUMP_OBJECTIVES or DUMP_ASSIGNED_MOVES:
                print(agent.call_sign)
            if DUMP_OBJECTIVES:
                print('\t', agent.objectives)
            if DUMP_ASSIGNED_MOVES:
                print('\t', agent.assigned_move)

        self.iterations += 1

    def update_agents(self, enemy_units, friendly_units):
        enemy_damage_counter_prediction = {e.call_sign: DamageCounter(e) for e in enemy_units}
        for a, f in zip(self.agents, friendly_units):
            a.update(f, enemy_units, self.damage_map, enemy_damage_counter_prediction)

    def get_control_point_by_position(self, world, pos):
        cp = world.get_nearest_control_point(pos)
        if cp.position != pos:
            raise 'Invalid position for control point'
        return cp


def get_max_clearance(world, x, y):
    max_clearance = 0
    directions = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, 1], [1, -1], [-1, -1]]
    for d in directions:
        this_clearance = 1
        while world.get_tile(
                (x + d[0] * this_clearance, y + d[1] * this_clearance)) != TileType.WALL and this_clearance < 11:
            this_clearance += 1
        max_clearance = max(max_clearance, this_clearance - 1)
    return max_clearance


def pretty_print_matrix(matrix):
    s = [[str(e) for e in row] for row in matrix]
    lens = [max(map(len, col)) for col in zip(*s)]
    fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
    table = [fmt.format(*row) for row in s]
    print('\n'.join(table))
