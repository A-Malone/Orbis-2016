from collections import defaultdict
import itertools

from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *

class DamageMap(object):
    """ Object which stores a dictionary of position to (damage, range) pairs for use in threat analysis"""

    GAMMA = 0.9
    MAX_TURN = 5

    def __init__(self):
        pass

    def update_map(self, world, enemy_units):
        self.damage_map = defaultdict(list)
        self.width = world.width
        self.height = world.height
        self.world = world

        for i, enemy in enumerate(enemy_units):
            self.accumulate_enemy_map(world, enemy)

    def accumulate_enemy_map(self, world, enemy):
        range_dict = dict()        
        ex, ey = enemy.position
        
        erange = WeaponType.get_range(enemy.current_weapon_type)
        damage = WeaponType.get_damage(enemy.current_weapon_type)

        for p0 in itertools.product(range(ex - 1, ex + 2), range(ey - 1, ey + 2)):            
            start_tile = world.get_tile(p0)
            if (start_tile and not start_tile.does_block_bullets()):

                # Pick direction
                for dx, dy in itertools.product(range(- 1,2), range(-1,2)):
                    if(dx == dy == 0):
                        continue
                    else:
                        # Raycast out
                        for d in range(erange):
                            p = PointUtils.add_points(PointUtils.scale_point((dx, dy), d), p0)
                            tile = world.get_tile(p)
                            if (tile):
                                if(tile.does_block_bullets()):
                                    break
                                elif(p in range_dict and range_dict[p] <= d):
                                    # Break if we've already been here in less moves
                                    break
                                else:
                                    range_dict[p] = d

        # Update the cost map with the range values
        for p, k in range_dict:
            self.damage_map[p].append((damage, erange))

    def cost(self, unit, pos, turn):
        if turn > self.MAX_TURN:
            return 0

        tile_data = self.damage_map[pos]

        weapon_range = WeaponType.get_range(unit.current_weapon_type)
        weapon_damage = WeaponType.get_damage(unit.current_weapon_type)

        damage_delta = sum((d for (d,r) in tile_data))*len(tile_data)
        if (any((r <= weapon_range for (d,r) in tile_data))):
            damage_delta -= weapon_damage

        return damage_delta*self.GAMMA**turn
