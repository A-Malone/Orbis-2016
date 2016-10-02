class DamageCounter():
    def __init__(self, target):
        self.target = target
        self.cum_damage = 0
        self.attackers = []

    def add_damage(self, agent):
        self.cum_damage += agent.current_weapon_type.get_damage()
        self.attackers.append(agent)

    def get_total_damage(self):
        return self.cum_damage * len(self.attackers)

    def __repr__(self):
        return str(self.get_total_damage())
