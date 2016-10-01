from queue import Queue, PriorityQueue
from PythonClientAPI.libs.Game import PointUtils

from functools import total_ordering
import itertools
import sys

# Path cost
def path_cost(path, damage_map):
    cost = 0
    for state in path:
        cost += step_cost(None, state, damage_map, None)
    return cost

# Cost of a single step
def step_cost(unit, pos, damage_map, turn):
    return 1 + damage_map.cost(unit, pos, turn)

def reconstruct_path(came_from, state_data_map, end):
    state = end
    path = []

    while (state in came_from):
        new_state = came_from[state]
        path.append(state)
        state = new_state

    return path

class Path(object):
    """docstring for Path"""
    def __init__(self, path_list, cost):
        super(Path, self).__init__()
        self.path_list = path_list
        self.cost = cost

@total_ordering
class AStarData(object):
    def __init__(self, state, g, h, turn):
        self.state = state
        self.g = g
        self.h = h
        self.turn = turn

    def f(self):
        return self.g + self.h

    def __lt__(self, other):
        return self.f() < other.f()

class AStar(object):
    """docstring for AStar"""

    def __init__(self):
        super(AStar, self).__init__()

        self.open_set = set()
        self.closed_set = set()

        # Stores astardata references
        self.open_queue = PriorityQueue()

        self.came_from = {}

        self.state_data_map = {}

    def get_neighbours(self, state, damage_map):
        for p in itertools.product(range(state[0]-1, state[0]+2), range(state[1]-1, state[1]+2)):            
            if (damage_map.can_move_to(p)):
                yield p

    def get_or_create_data(self, state):
        data = self.state_data_map.get(state, None)
        if (data == None):
            data = AStarData(state, 0, 0, 0)
            self.state_data_map[state] = data

        return data

    def heuristic(self, state1, state2):
        return PointUtils.chebyshev_distance(state1, state2)

    def get_path(self, unit, start, end, damage_map):
        start_data = AStarData(start, 0, self.heuristic(start, end), 0)
        self.state_data_map[start] = start_data
        self.open_queue.put(start_data)

        self.open_set.add(start)

        path = None

        while (not self.open_queue.empty()):
            # Get the first item in the min-heap
            current_data = self.open_queue.get()
            current = current_data.state
            self.open_set.remove(current)

            # Short-circuit for the end
            if (current == end):
                path_list = reconstruct_path(self.came_from, self.state_data_map, current)
                while(path_list and path_list[-1] == start):
                    path_list.pop()
                path = Path(path_list, current_data.g)
                break

            self.closed_set.add(current);

            for neighbour in self.get_neighbours(current, damage_map):

                # If it's in the closed set skip
                if (neighbour in self.closed_set):
                    continue

                # The distance from start to goal passing through current and the neighbour.
                neighbour_data = self.get_or_create_data(neighbour)

                tentative_g_score = current_data.g + step_cost(unit, neighbour, damage_map, current_data.turn + 1)
                if (neighbour in self.open_set and tentative_g_score >= neighbour_data.g):
                    continue        # This is not a better path.

                # This path is the best until now. Record it!
                self.came_from[neighbour] = current;

                neighbour_data.g = tentative_g_score
                neighbour_data.h = self.heuristic(neighbour, end)
                neighbour_data.turn = current_data.turn + 1

                if (not neighbour in self.open_set):
                    self.open_set.add(neighbour)
                    self.open_queue.put(neighbour_data)

        if (path == None):
            print("No solution")

        return path