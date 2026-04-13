"""
PERSON 2: Scheduler (SSGS + priority rules)
=============================================
Core scheduling engine for RCPSP.

Main idea:
- an optimizer proposes a precedence-feasible activity list
- SSGS turns that list into a feasible schedule
- makespan is the start time of the dummy end activity
"""

from functools import lru_cache
from models import Project, Activity


class ResourceTracker:
    """
    Tracks renewable resource usage over time.
    usage[t][k] = amount of resource k used at time t
    """

    def __init__(self, capacities):
        self.capacities = capacities
        self.k = len(capacities)
        self.usage = {}

    def is_feasible(self, activity, start_time):
        """Check whether activity can run from start_time without exceeding capacity."""
        if activity.duration == 0:
            return True

        for t in range(start_time, start_time + activity.duration):
            usage_at_t = self.usage.get(t)
            if usage_at_t is None:
                continue
            for k in range(self.k):
                if usage_at_t[k] + activity.resources[k] > self.capacities[k]:
                    return False
        return True

    def book(self, activity, start_time):
        """Reserve resources for the full duration of activity."""
        if activity.duration == 0:
            return

        for t in range(start_time, start_time + activity.duration):
            if t not in self.usage:
                self.usage[t] = [0] * self.k
            for k in range(self.k):
                self.usage[t][k] += activity.resources[k]


def find_earliest_start(project, activity_id, schedule, tracker):
    """
    Earliest feasible start time for activity_id:
    1. respect predecessors
    2. scan forward until resources fit

    Also detects structurally impossible activities so batch mode does not hang forever.
    """
    activity = project.activities[activity_id]

    # impossible activity check
    for k in range(project.k):
        if activity.resources[k] > project.capacities[k]:
            raise ValueError(
                f"Activity {activity_id} impossible: "
                f"needs R{k+1}={activity.resources[k]} > capacity {project.capacities[k]}"
            )

    earliest = 0
    for pred_id in project.predecessors[activity_id]:
        pred = project.activities[pred_id]
        earliest = max(earliest, schedule[pred_id] + pred.duration)

    if activity.duration == 0:
        return earliest

    t = earliest
    while not tracker.is_feasible(activity, t):
        t += 1
    return t


def ssgs(project, activity_list):
    """
    Serial Schedule Generation Scheme.
    activity_list must be precedence-feasible.
    returns: dict {activity_id: start_time}
    """
    tracker = ResourceTracker(project.capacities)
    schedule = {}

    schedule[0] = 0
    tracker.book(project.activities[0], 0)

    for act_id in activity_list:
        start = find_earliest_start(project, act_id, schedule, tracker)
        schedule[act_id] = start
        tracker.book(project.activities[act_id], start)

    end_id = project.n + 1
    schedule[end_id] = find_earliest_start(project, end_id, schedule, tracker)
    return schedule


def get_makespan(project, schedule):
    """Makespan = start time of the dummy end activity."""
    return schedule.get(project.n + 1, -1)


# ========================================
# TOPOLOGICALLY SAFE PRIORITY RULES
# ========================================

def _topo_priority_order(project, priority_key):
    """
    Generic topological traversal:
    at each step choose the eligible activity with minimum priority_key(act_id).
    Guarantees precedence-feasible output.
    """
    import heapq

    placed = {0}
    remaining = set(project.real_ids())
    activity_list = []
    heap = []

    for act_id in remaining:
        if all(p in placed for p in project.predecessors[act_id]):
            heapq.heappush(heap, (priority_key(act_id), act_id))

    while remaining:
        while heap:
            _, act_id = heapq.heappop(heap)
            if act_id in remaining:
                break
        else:
            # safety fallback
            eligible = [i for i in remaining if all(p in placed for p in project.predecessors[i])]
            if not eligible:
                raise ValueError("No eligible activity found; precedence graph may be invalid")
            act_id = min(eligible)

        activity_list.append(act_id)
        placed.add(act_id)
        remaining.remove(act_id)

        for succ_id in project.successors[act_id]:
            if succ_id in remaining and all(p in placed for p in project.predecessors[succ_id]):
                heapq.heappush(heap, (priority_key(succ_id), succ_id))

    return activity_list


def order_by_id(project):
    """
    Smallest eligible ID first.
    Topologically safe replacement for raw numeric order.
    """
    return _topo_priority_order(project, lambda i: i)


def order_by_duration(project):
    """Shortest duration first among eligible activities."""
    return _topo_priority_order(project, lambda i: (project.activities[i].duration, i))


@lru_cache(maxsize=None)
def _dummy_cache_key(x):
    return x


def order_by_successors(project):
    """Most total downstream successors first."""
    total_succs = {}

    def count_succs(act_id):
        if act_id in total_succs:
            return total_succs[act_id]
        seen = set()
        stack = list(project.successors[act_id])
        while stack:
            cur = stack.pop()
            if cur in seen or cur == project.n + 1:
                continue
            seen.add(cur)
            stack.extend(project.successors[cur])
        total_succs[act_id] = len(seen)
        return total_succs[act_id]

    for act_id in project.all_ids():
        count_succs(act_id)

    return _topo_priority_order(project, lambda i: (-total_succs[i], i))


def compute_lft(project):
    """
    Resource-free latest finish times using forward/backward passes.
    """
    in_degree = {i: len(project.predecessors[i]) for i in project.all_ids()}
    queue = [0]
    topo = []

    while queue:
        node = queue.pop(0)
        topo.append(node)
        for succ in project.successors[node]:
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    est = {0: 0}
    for act_id in topo:
        act = project.activities[act_id]
        for succ_id in project.successors[act_id]:
            est[succ_id] = max(est.get(succ_id, 0), est[act_id] + act.duration)

    end_id = project.n + 1
    makespan_ub = est.get(end_id, 0)

    lft = {end_id: makespan_ub}
    for act_id in reversed(topo):
        if act_id == end_id:
            continue
        best = makespan_ub
        for succ_id in project.successors[act_id]:
            succ_dur = project.activities[succ_id].duration
            best = min(best, lft.get(succ_id, makespan_ub) - succ_dur)
        lft[act_id] = best

    return lft


def order_by_lft(project):
    """Smallest latest-finish-time first among eligible activities."""
    lft = compute_lft(project)
    return _topo_priority_order(project, lambda i: (lft.get(i, float("inf")), i))


def order_by_positional_weight(project):
    """
    Largest positional weight first:
    own duration + durations of all downstream activities.
    """
    pw = {}

    def positional_weight(act_id):
        if act_id in pw:
            return pw[act_id]
        total = project.activities[act_id].duration
        seen = set()
        stack = list(project.successors[act_id])
        while stack:
            cur = stack.pop()
            if cur in seen or cur == project.n + 1:
                continue
            seen.add(cur)
            total += project.activities[cur].duration
            stack.extend(project.successors[cur])
        pw[act_id] = total
        return total

    for act_id in project.real_ids():
        positional_weight(act_id)

    return _topo_priority_order(project, lambda i: (-pw[i], i))


def order_by_resource_demand(project):
    """
    Largest total resource demand first.
    """
    return _topo_priority_order(
        project,
        lambda i: (-sum(project.activities[i].resources), -project.activities[i].duration, i)
    )


def order_by_bottleneck(project):
    """
    Bottleneck-weighted resource demand first.
    Resources with smaller capacities get larger weights.
    """
    weights = [1.0 / max(1, c) for c in project.capacities]

    def score(i):
        act = project.activities[i]
        weighted = sum(act.resources[k] * weights[k] for k in range(project.k))
        return (-weighted, -act.duration, i)

    return _topo_priority_order(project, score)


if __name__ == "__main__":
    from parser import parse
    import os

    path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP1.SCH")
    proj = parse(path)
    order = order_by_lft(proj)
    schedule = ssgs(proj, order)
    print("order:", order)
    print("makespan:", get_makespan(proj, schedule))