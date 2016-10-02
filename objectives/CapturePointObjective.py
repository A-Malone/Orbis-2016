from . import Objective

class AttackCapturePointObjective(Objective):
    def __init__(self, control_point):
        super().__init__(control_point.position)
        self.control_point = control_point
    
    def update(self, world, enemy_units, friendly_units):
        super().update(world, enemy_units, friendly_units)
        self.complete = (self.control_point.controlling_team == friendly_units[0].team)


class DefendCapturePointObjective(Objective):
    THRESHOLD = 10 

    def __init__(self, control_point):
        super().__init__(control_point.position)
        self.control_point = control_point

    def update(self, world, enemy_units, friendly_units):
        super().update(world, enemy_units, friendly_units)
        self.complete = self.net_score > self.THRESHOLD