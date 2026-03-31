"""
shared data stuff that everyone will use
just import from here can alr
"""

from dataclasses import dataclass, field


@dataclass
class Activity:
    id: int
    duration: int
    resources: list  # how much of each resource this activity needs


@dataclass
class Project:
    n: int              # num of real activities (not counting the dummy start/end)
    k: int              # num of resource types
    activities: dict    # activity_id -> Activity obj
    successors: dict    # activity_id -> list of (successor_id, lag)
    predecessors: dict  # activity_id -> list of (predecessor_id, lag)
    capacities: list    # max units for each resource type

    def all_ids(self):
        """0 to n+1 (includes dummy start and end)"""
        return list(range(self.n + 2))

    def real_ids(self):
        """1 to n only (no dummies)"""
        return list(range(1, self.n + 1))
