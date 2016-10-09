from PythonClientAPI.libs.Game.Enums import *
from . import Objective

MAP_OPENESS_AGGREGATE_THRESHOLD = 25

def weapon_priority(pickup_type, map_openess_aggregate):
        if (map_openess_aggregate > MAP_OPENESS_AGGREGATE_THRESHOLD):
            if pickup_type == PickupType.WEAPON_SCATTER_GUN:
                return 0.5
            elif pickup_type == PickupType.WEAPON_RAIL_GUN:
                return 2            
        elif map_openess_aggregate < MAP_OPENESS_AGGREGATE_THRESHOLD / 2:
            if pickup_type == PickupType.WEAPON_SCATTER_GUN:
                return 2        
        return 1

class PickupObjective(Objective):

    BASE_PRIORITY = 2
    GUN_BONUS = 2

    def __init__(self, position, pickup_type, map_openess_aggregate):
        super().__init__(position)
        self.pickup_type = pickup_type
        self.map_openess_aggregate = map_openess_aggregate

    def update(self, world, enemy_units, friendly_units):
        super().update(world, enemy_units, friendly_units)
        self.complete = (world.get_pickup_at_position(self.position) == None)

        self.priority = self.BASE_PRIORITY
        if (self.pickup_type in (PickupType.WEAPON_LASER_RIFLE, PickupType.WEAPON_RAIL_GUN, PickupType.WEAPON_SCATTER_GUN)):
            self.priority *= self.GUN_BONUS * weapon_priority(self.pickup_type, self.map_openess_aggregate)


def is_weapon_objective(obj):
    return isinstance(obj, PickupObjective) and obj.pickup_type in (PickupType.WEAPON_LASER_RIFLE, PickupType.WEAPON_RAIL_GUN, PickupType.WEAPON_SCATTER_GUN)
