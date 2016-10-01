from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
import itertools
import time
from Agent import Agent
from Objective import Objective

DUMP_OBJECTIVES = True
DUMP_ASSIGNED_MOVES = False

from damage_map import DamageMap
from astar import AStar


class PlayerAI:
    def __init__(self):
        self.iterations = 0
        self.clearances = []
        self.agents = [Agent() for i in range(4)]
        self.damage_map = DamageMap()

    def do_move(self, world, enemy_units, friendly_units):
        """
        This method will get called every turn; Your glorious AI code goes here.
        
        :param World world: The latest state of the world.
        :param list[EnemyUnit] enemy_units: An array of all 4 units on the enemy team. Their order won't change.
        :param list[FriendlyUnit] friendly_units: An array of all 4 units on your team. Their order won't change.
        """

        self.update_agents(friendly_units)
        self.damage_map.update_map(world, enemy_units)

        print("iteration: {}".format(self.iterations))
        if self.iterations == 0:
            self.team = friendly_units[0].team
            self.clearances = [[0 for x in range(world.width)] for y in range(world.height)]
            for x, y in itertools.product(range(world.width), range(world.height)):
                tile_type = world.get_tile((x, y));
                if tile_type == TileType.WALL:
                    continue
                self.clearances[y][x] = get_max_clearance(world, x, y)
            pretty_print_matrix(self.clearances)

        # Rank control points in terms of influence
        control_point_scores = []
        for cp in world.control_points:
            friendly_distances = sorted(0.5 ** world.get_path_length(f.position, cp.position) for f in friendly_units)
            enemy_distances = sorted(0.5 ** world.get_path_length(e.position, cp.position) for e in enemy_units)
            control_point_scores.append(
                (cp, sum(friendly_distances) - sum(enemy_distances)))  # TODO: Figure out something better?
        control_point_scores.sort(key=lambda c: c[1], reverse=True)

        # For each control point we have that isn't already ours, in order of influence
        for cp, score in filter(lambda c: c[0].controlling_team != self.team, control_point_scores):
            for agent in sorted(filter(lambda a: len(a.objectives) == 0, self.agents),
                                key=lambda a: world.get_path_length(a.position, cp.position)):
                agent.objectives.append(Objective(Objective.CONTROL_POINT, cp.position))
                break

        for agent in self.agents:
            agent.do_move(world, enemy_units, friendly_units)
            if DUMP_OBJECTIVES or DUMP_ASSIGNED_MOVES:
                print(agent.call_sign)
            if DUMP_OBJECTIVES:
                print('\t', agent.objectives)
            if DUMP_ASSIGNED_MOVES:
                print('\t', agent.assigned_move)


    self.iterations += 1

    def update_agents(self, friendly_units):
        for a, f in zip(self.agents, friendly_units):
            a.update(f)


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
