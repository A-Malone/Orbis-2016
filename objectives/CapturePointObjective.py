from . import Objective

class AttackCapturePointObjective(Objective):

    BASE_PRIORITY = 10
    NO_MAINFRAME = 5

    def __init__(self, position, control_point_index, centrality):
        super().__init__(position)
        self.control_point_index = control_point_index
        self.centrality = centrality

    def update(self, world, enemy_units, friendly_units):
        super().update(world, enemy_units, friendly_units)
        control_point = world.control_points[self.control_point_index]
        self.complete = (control_point.controlling_team == friendly_units[0].team)

        # Calculate priority
        self.priority = self.BASE_PRIORITY * self.centrality
        if (world.control_points[self.control_point_index].is_mainframe): 
            if(not any(filter(lambda x: x.is_mainframe and x.controlling_team == friendly_units[0].team, world.control_points))):
                self.priority *= self.NO_MAINFRAME


class DefendCapturePointObjective(Objective):
    THRESHOLD = 5

    def __init__(self, position, control_point_index):
        super().__init__(position)
        self.control_point_index = control_point_index

    def update(self, world, enemy_units, friendly_units):
        super().update(world, enemy_units, friendly_units)
        control_point = world.control_points[self.control_point_index]
        self.complete = (self.net_score > self.THRESHOLD or control_point.controlling_team != friendly_units[0].team)
