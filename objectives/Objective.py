from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
from functools import total_ordering


@total_ordering
class Objective():
    def __init__(self, position):
        self.position = position

        self.difficulty = 0
        self.priority = 0

        self.agent_set = set()
        self.complete = False

    def update(self, world, enemy_units, friendly_units):
        friendly_distances = (world.get_path_length(f.position, self.position) for f in friendly_units)
        enemy_distances = (world.get_path_length(e.position, self.position) for e in enemy_units)

        friendly_score = sum(friendly_distances)
        enemy_score = sum(enemy_distances)
        self.difficulty =  friendly_score / enemy_score

    def __lt__(self, other):
        if (self.priority == other.priority):
            return self.difficulty < other.difficulty
        return self.priority > other.priority