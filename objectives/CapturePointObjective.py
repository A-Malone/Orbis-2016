from . import Objective

class AttackCapturePointObjective(Objective):
    def __init__(self, position, control_point_index):
        super().__init__(position)
        self.control_point_index = control_point_index
    
    def update(self, world, enemy_units, friendly_units):
        super().update(world, enemy_units, friendly_units)
        control_point = world.control_points[self.control_point_index]
        self.complete = (control_point.controlling_team == friendly_units[0].team)


class DefendCapturePointObjective(Objective):
    THRESHOLD = 10

    def __init__(self, position, control_point_index):
        super().__init__(position)
        self.control_point_index = control_point_index

    def update(self, world, enemy_units, friendly_units):
        super().update(world, enemy_units, friendly_units)
        control_point = world.control_points[self.control_point_index]
        self.complete = (self.net_score > self.THRESHOLD or control_point.controlling_team != friendly_units[0].team)