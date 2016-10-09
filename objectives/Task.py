from functools import total_ordering

@total_ordering
class Task(object):
    def __init__(self, agent, objective):
        self.agent = agent
        self.objective

    def update(self, world):
        self.difficulty = self.objective.difficulty * world.get_path_length(agent.position, objective.position)
        self.priority = self.objective.priority
        self.score = self.priority - self.difficulty

    def __lt__(self, other):
        return  self.score < other.score