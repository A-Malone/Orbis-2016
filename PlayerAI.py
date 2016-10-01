from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *

from damage_map import DamageMap
from astar import AStar


class PlayerAI:
    def __init__(self):
        self.damage_map = DamageMap()

    def do_move(self, world, enemy_units, friendly_units):
        """
        This method will get called every turn; Your glorious AI code goes here.
        
        :param World world: The latest state of the world.
        :param list[EnemyUnit] enemy_units: An array of all 4 units on the enemy team. Their order won't change.
        :param list[FriendlyUnit] friendly_units: An array of all 4 units on your team. Their order won't change.
        """
        self.damage_map.update_map(world, enemy_units)

        for unit in friendly_units:
            if (unit.position != (1,1)):
                astar = AStar()
                path = astar.get_path(unit, unit.position, (1,1), self.damage_map)
                unit.move_to_destination(path.path_list[-1])