import src.NEAT.NeatProperties as Props


class Species:
    def __init__(self, representative):
        self.representative = representative
        self.members = [representative]

    def add_member(self, new_member, thresh=Props.DISTANCE_THRESH):
        if self.is_compatible(new_member, thresh):
            self.members.append(new_member)

    def is_compatible(self, individual, thresh=Props.DISTANCE_THRESH, c1=1, c2=1):
        return self.representative.distance_to(individual, c1, c2) <= thresh

    def clear(self):
        self.members.clear()
