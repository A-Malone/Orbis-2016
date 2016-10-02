from . import Objective

class EnemyObjective(Objective):
    def __init__(self, position, enemy_index):
        super().__init__(position)
        self.enemy_index = enemy_index

    def update(self, world, enemy_units, friendly_units):
        enemy = enemy_units[self.enemy_index]
        self.position = enemy.position
        self.complete = (enemy.health == 0)
        super().update(world, enemy_units, friendly_units)