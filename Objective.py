from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *


class Objective():
    CONTROL_POINT = 0
    PICK_UP = 1
    WIN_GAME = 2

    def __init__(self, type, position):
        self.type = type
        self.position = position
        self.score = 0
        self.complete = False

    def __repr__(self):
        _names = {Objective.CONTROL_POINT: 'Control Point', Objective.PICK_UP: 'Pick up',
                  Objective.WIN_GAME: 'Win game'}
        return str(_names[self.type]) + ' ' + (str(self.position) if self.position else '') + ' ' + str(
            self.score) + (' Complete' if self.complete else '')
