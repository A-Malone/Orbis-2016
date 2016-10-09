from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
import itertools
import time
from collections import defaultdict
from queue import PriorityQueue

from Agent import Agent
from DamageCounter import DamageCounter
from objectives import *
from damage_map import DamageMap
from astar import AStar
import traceback

DUMP_OBJECTIVES = False
DUMP_ASSIGNED_MOVES = False
MAP_OPENESS_AGGREGATE_THRESHOLD = 25

# The number of steps out of its path an agent will go to get an objective
PATH_PICKUP_DISTANCE = 1


class PlayerAI:
    def __init__(self):
        self.iterations = 0
        self.clearances = []
        self.agents = [Agent() for i in range(4)]
        self.damage_map = DamageMap()

        # Priority queue does not make sense because priorities change
        self.global_objectives = list()
        self.objectives = set()
        
        # Pickup objectives are tasks en-route to objectives
        self.agent_task_list_map = {}

        self.position_to_cp_objective_map = {}
        self.index_to_enemy_objective_map = {}
        self.position_to_pickup_objective_map = {}

    def do_move(self, world, enemy_units, friendly_units):
        """
        This method will get called every turn; Your glorious AI code goes here.

        :param World world: The latest state of the world.
        :param list[EnemyUnit] enemy_units: An array of all 4 units on the enemy team. Their order won't change.
        :param list[FriendlyUnit] friendly_units: An array of all 4 units on your team. Their order won't change.
        """

        # ---- First time map analysis
        # ----------------------------------------
        print("iteration: {}".format(self.iterations))
        if self.iterations == 0:
            self.team = friendly_units[0].team
            self.analyze_map(world)
            self.agent_task_list_map = {agent : []}

        # ---- UPDATES
        # ----------------------------------------
        self.damage_map.update_map(world, enemy_units)
        self.update_agents(enemy_units, friendly_units)

        # ---- UPDATE CURRENT OBJECTIVES
        # ----------------------------------------

        # Update objective scores, and perform update logic
        for obj in self.objectives:
            obj.update(world, enemy_units, friendly_units)

        # Filter out complete objectives
        self.objectives = set(filter(lambda x : not x.complete, self.objectives))

        for agent in self.agents:
            agent.update_objectives()
            if (agent.health == 0):
                for obj in agent.objectives:
                    if (agent in obj.agent_set):
                        obj.agent_set.remove(agent)
                
                agent.objectives = []
                agent.objective_max_priority = 0

        # ---- IDENTIFY AND UPDATE NEW OBJECTIVES
        # ----------------------------------------

        # Global objectives
        new_objs = []        
        for i, control_point in enumerate(world.control_points):
            cp_obj = self.position_to_cp_objective_map.get(control_point.position, None)
            if (not cp_obj or cp_obj.complete == True):
                if (control_point.controlling_team == self.team):
                    pass
                    # new_obj = DefendCapturePointObjective(control_point.position, i)
                else:
                    new_obj = AttackCapturePointObjective(control_point.position, i, self.centrality[i])
                    new_objs.append(new_obj)
                    self.position_to_cp_objective_map[new_obj.position] = new_obj

        # Update objective scores, and perform update logic, and the new objectives
        for obj in new_objs:            
            obj.update(world, enemy_units, friendly_units)
            self.global_objectives.append(obj)
            self.objectives.add(obj)

        # Subtasks
        new_task_objectives = []
        for item in world.pickups:
            item_obj = self.position_to_pickup_objective_map.get(item.position, None)

            if (not item_obj or item_obj.complete == True):
                new_obj = PickupObjective(item.position, item.pickup_type, self.map_openess_aggregate)
                self.position_to_pickup_objective_map[item.position] = new_obj
                new_task_objectives.append(new_obj)

        for task_obj in new_task_objectives:
            for agent in self.agents:                
                task = Task(agent, task_obj)
                task_obj.update(world, enemy_units, friendly_units)
                task.update(world)
                self.agent_task_list_map[agent].append(task)

        # Enemy Objectives
        # for i, enemy in enumerate(enemy_units):
        #     enemy_obj = self.index_to_enemy_objective_map.get(i, None)

        #     if (not enemy_obj or enemy_obj.complete == True):
        #         new_obj = EnemyObjective(enemy.position, i)
        #         self.index_to_enemy_objective_map[i] = new_obj
        #         new_objs.append(new_obj)
        

        for agent in self.agents:
            self.agent_task_list_map[agent].sort()



        # ---- LOAD BALANCE
        # ----------------------------------------
        # for obj in filter(lambda o: len(o.agent_set) > 1, self.objectives):
        #     # If an objective has more than one agent associated with it, free them up
        #     repo_agents = list(obj.agent_set)[1:]
        #     for agent in repo_agents:
        #         agent.objectives.remove(obj)
        #         obj.agent_set.remove(agent)

        # ---- ORDER AND ASSIGN OBJECTIVES
        # ----------------------------------------       
        available_agents = set(filter(lambda x: x.health > 0, self.agents))

        # ---- ORDER AND ASSIGN OBJECTIVES
        # ----------------------------------------


        # Iterate over the objectives in order of priority
        for obj in reversed(self.global_objectives):            

            # If it's complete or someone is already on it, skip
            if (obj.complete or obj.agent_set):
                continue

            # Do any agents have lower priority tasks?            
            if (any(filter(lambda x: x.objective_max_priority < obj.priority))):
                
                valid_agents = filter(lambda x: x.objective_max_priority < obj.priority)

                # Assign objective to the most suitable agent
                for agent in sorted(valid_agents, key=lambda a: world.get_path_length(a.position, obj.position)):                
                    
                    if(agent.objectives):
                        print("Reassigning agent: {} - {}".format(obj.priority, obj))
                        for i in agent.objectives:
                            if (agent in i.agent_set):
                                i.agent_set.remove(agent)
                        
                    #print("Assigning {} priority {} objective {}".format(agent.call_sign, obj.priority, obj))
                    agent.objectives = [obj]
                    agent.objective_max_priority = obj.priority                                        
                    obj.agent_set.add(agent)
                    available_agents.remove(agent)                    

        # ---- DO OBJECTIVES
        # ----------------------------------------

        # Agents do what they have been assigned
        for agent in self.agents:
            agent.do_objectives(world, enemy_units, friendly_units)
            if DUMP_OBJECTIVES or DUMP_ASSIGNED_MOVES:
                print(agent.call_sign)
            if DUMP_OBJECTIVES:
                print('\t', agent.objectives)
            if DUMP_ASSIGNED_MOVES:
                print('\t', agent.assigned_move)

        self.iterations += 1

    def update_agents(self, enemy_units, friendly_units):
        enemy_damage_counter_prediction = {e.call_sign: DamageCounter(e) for e in enemy_units}
        for a, f in zip(self.agents, friendly_units):
            a.update(f, enemy_units, self.damage_map, enemy_damage_counter_prediction)

    def get_control_point_by_position(self, world, pos):
        cp = world.get_nearest_control_point(pos)
        if cp.position != pos:
            traceback.print_tb()
        return cp

    def get_max_clearance(self, world, x, y):
        max_clearance = 0
        directions = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, 1], [1, -1], [-1, -1]]
        for d in directions:
            this_clearance = 1
            while world.get_tile(
                    (x + d[0] * this_clearance, y + d[1] * this_clearance)) != TileType.WALL and this_clearance < 11:
                this_clearance += 1
            max_clearance = max(max_clearance, this_clearance - 1)
        return max_clearance

    def weapon_priority(self, pickup_type):
        if (self.map_openess_aggregate > MAP_OPENESS_AGGREGATE_THRESHOLD):
            if pickup_type == PickupType.WEAPON_SCATTER_GUN:
                return 0.1
            elif pickup_type == PickupType.WEAPON_RAIL_GUN:
                return 10
            else:
                return 1
        elif self.map_openess_aggregate < MAP_OPENESS_AGGREGATE_THRESHOLD / 2:
            if pickup_type == PickupType.WEAPON_SCATTER_GUN:
                return 10
            else:
                return 1
        else:
            return 1

    def analyze_map(self, world):        
        self.clearances = [[0 for x in range(world.width)] for y in range(world.height)]
        for x, y in itertools.product(range(world.width), range(world.height)):
            tile_type = world.get_tile((x, y));
            if tile_type == TileType.WALL:
                continue
            self.clearances[y][x] = self.get_max_clearance(world, x, y)
        self.map_openess_aggregate = sum(map(lambda x: sum(n ** 2 for n in x), self.clearances)) / sum(
            map(len, self.clearances))

        print("OPENNESS " + str(self.map_openess_aggregate))

        # Control point centrality scores
        self.centrality = [1 / sum(map(lambda x: world.get_path_length(x.position, cp.position), world.control_points)) for cp in world.control_points]
        max_centrality = max(self.centrality)
        for i in range(len(self.centrality)):
            self.centrality[i] /= max_centrality
