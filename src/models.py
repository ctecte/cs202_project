from dataclasses import dataclass, field

@dataclass
class Activity:
    id: int
    duration: int
    resources: list  # how much of each resource this activity needs


@dataclass
class Project:
    n: int              # num of real activities
    k: int              # num of resource types
    activities: dict    # activity_id to obj mapping
    successors: dict    # activity successors successor_id
    predecessors: dict  # activity_id dependencies required predecessor_ids
    capacities: list    # max units for each resource type

    # 0 to n+1 (includes dummy start and end)
    def all_ids(self):
        return list(range(self.n + 2))

    # 1 to n (no dummies)
    def real_ids(self):
        return list(range(1, self.n + 1))
