from . import Objective

class PickupObjective(Objective):
    def __init__(self, position, pickup_type):
        super().__init__(position)
        self.pickup_type = pickup_type

    def update(self, world, enemy_units, friendly_units):
        super().update(world, enemy_units, friendly_units)
        self.complete = (world.get_pickup_at_position(self.position) == None)