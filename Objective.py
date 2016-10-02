from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *


class Objective():
    CONTROL_POINT = 0
    PICK_UP = 1

    _names = {CONTROL_POINT: 'Control Point', PICK_UP: 'Pick up'}

    def __init__(self, type, position):
        self.type = type
        self.position = position
        self.score = 0
        self.complete = False

    def __repr__(self):
        return str(self._names[self.type]) + ' ' + str(self.position) + ' ' + str(
            self.score) + (' Complete' if self.complete else '')
