from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *


class Objective():
    def __init__(self, position):
        self.position = position
        
        self.friendly_score = 0
        self.enemy_score = 0
        self.net_score = 0

        self.agent_set = set()

        self.complete = False

    def update(self, world, enemy_units, friendly_units):
        try:
            friendly_distances = (0.5 ** world.get_path_length(f.position, self.position) for f in friendly_units)
            enemy_distances = (0.5 ** world.get_path_length(e.position, self.position) for e in enemy_units)

            self.friendly_score = sum(friendly_distances)
            self.enemy_score = sum(enemy_distances)
            self.net_score =  self.friendly_score - self.enemy_score
        except e:
            traceback.print_exc()