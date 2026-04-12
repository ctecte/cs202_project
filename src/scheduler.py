"""
Scheduler: SSGS (Serial Schedule Generation Scheme) + priority rules.
Optimized for speed — SSGS is called thousands of times during optimization.
"""

from models import Project, Activity


class ResourceTracker:
    """
    Tracks resource usage at each time step.
    Maintains a sorted set of 'event times' (when activities start/finish)
    so we can jump to relevant times instead of scanning +1.
    """

    def __init__(self, capacities):
        self.capacities = capacities
        self.k = len(capacities)
        self.usage = {}  # t -> [r1, r2, ..., rk]
        self.finish_times = set()  # times when any activity finishes

    def is_feasible(self, resources, start_time, duration):
        """
        Check if we can place an activity with given resources at start_time
        for the given duration without exceeding capacity.
        """
        if duration == 0:
            return True
        end = start_time + duration
        for t in range(start_time, end):
            current = self.usage.get(t)
            if current is None:
                for r in range(self.k):
                    if resources[r] > self.capacities[r]:
                        return False
            else:
                for r in range(self.k):
                    if current[r] + resources[r] > self.capacities[r]:
                        return False
        return True

    def book(self, resources, start_time, duration):
        """Record resource usage over [start, start+duration)."""
        if duration == 0:
            return
        end = start_time + duration
        self.finish_times.add(end)
        for t in range(start_time, end):
            if t not in self.usage:
                self.usage[t] = [0] * self.k
            row = self.usage[t]
            for r in range(self.k):
                row[r] += resources[r]

    def find_earliest_feasible(self, resources, earliest, duration):
        """
        Find the earliest time >= earliest where the activity fits.
        Uses event-driven jumping: if infeasible at t, skip to the next
        event time (when some activity finishes and resources free up).
        """
        if duration == 0:
            return earliest

        # Check if demand can ever be satisfied
        for r in range(self.k):
            if resources[r] > self.capacities[r]:
                return earliest  # impossible, place anyway

        # Collect relevant event times >= earliest
        events = sorted(t for t in self.finish_times if t > earliest)

        t = earliest
        event_idx = 0

        while True:
            if self.is_feasible(resources, t, duration):
                return t
            # Jump to next event time
            while event_idx < len(events) and events[event_idx] <= t:
                event_idx += 1
            if event_idx < len(events):
                t = events[event_idx]
                event_idx += 1
            else:
                # No more events, scan linearly (shouldn't happen often)
                t += 1
                # Safety bound
                if t > earliest + 10000:
                    return t


def check_feasibility(project):
    """Check if the instance is feasible (no single activity exceeds any resource cap)."""
    for act_id in project.all_ids():
        act = project.activities[act_id]
        for r in range(project.k):
            if act.resources[r] > project.capacities[r]:
                return False
    return True


def ssgs(project, activity_list):
    """
    Serial Schedule Generation Scheme.
    activity_list: precedence-feasible ordering of real activity ids [1..n].
    Returns dict: activity_id -> start_time, or None if infeasible.
    """
    tracker = ResourceTracker(project.capacities)
    schedule = {}
    activities = project.activities
    predecessors = project.predecessors

    # schedule dummy start
    schedule[0] = 0
    act0 = activities[0]
    tracker.book(act0.resources, 0, act0.duration)

    # schedule each activity
    for act_id in activity_list:
        act = activities[act_id]

        # precedence: earliest = max(S_pred + d_pred)
        earliest = 0
        for pred_id in predecessors[act_id]:
            pred = activities[pred_id]
            val = schedule[pred_id] + pred.duration
            if val > earliest:
                earliest = val

        # resource: find earliest feasible from that point
        start = tracker.find_earliest_feasible(act.resources, earliest, act.duration)
        schedule[act_id] = start
        tracker.book(act.resources, start, act.duration)

    # schedule dummy end
    end_id = project.n + 1
    earliest = 0
    for pred_id in predecessors[end_id]:
        pred = activities[pred_id]
        val = schedule[pred_id] + pred.duration
        if val > earliest:
            earliest = val
    schedule[end_id] = earliest

    return schedule


def get_makespan(project, schedule):
    """Return the start time of the dummy end activity = makespan."""
    return schedule.get(project.n + 1, -1)


# ========================================
# PRIORITY RULES
# ========================================

def _priority_toposort(project, priority_key):
    """
    Topological sort of real activities [1..n] using a priority function.
    Among eligible activities (all preds placed), pick lowest priority_key.
    Guarantees precedence-feasible ordering.
    """
    import heapq
    placed = {0}
    result = []
    real = set(project.real_ids())
    end_id = project.n + 1
    successors = project.successors
    predecessors = project.predecessors

    heap = []
    for act_id in real:
        if all(p in placed for p in predecessors[act_id]):
            heapq.heappush(heap, (priority_key(act_id), act_id))

    while heap:
        _, act_id = heapq.heappop(heap)
        if act_id in placed:
            continue
        result.append(act_id)
        placed.add(act_id)

        for s in successors[act_id]:
            if s == end_id or s in placed or s not in real:
                continue
            if all(p in placed for p in predecessors[s]):
                heapq.heappush(heap, (priority_key(s), s))

    return result


def order_by_id(project):
    return _priority_toposort(project, lambda i: i)


def order_by_duration(project):
    return _priority_toposort(project, lambda i: project.activities[i].duration)


def _count_total_successors(project):
    cache = {}
    def dfs(act_id):
        if act_id in cache:
            return cache[act_id]
        total = set()
        for s in project.successors[act_id]:
            total.add(s)
            total.update(dfs(s))
        cache[act_id] = total
        return total
    for act_id in project.all_ids():
        dfs(act_id)
    return {aid: len(cache[aid]) for aid in project.all_ids()}


def order_by_successors(project):
    counts = _count_total_successors(project)
    return _priority_toposort(project, lambda i: -counts[i])


def _compute_lft(project):
    """Compute Latest Finish Time via forward + backward pass (precedence only)."""
    from collections import deque
    end_id = project.n + 1
    all_ids = project.all_ids()
    predecessors = project.predecessors
    successors = project.successors
    activities = project.activities

    in_degree = {i: len(predecessors[i]) for i in all_ids}
    queue = deque([i for i in all_ids if in_degree[i] == 0])
    est = {0: 0}
    topo_order = []

    while queue:
        u = queue.popleft()
        topo_order.append(u)
        if u not in est:
            est[u] = 0
        u_finish = est[u] + activities[u].duration
        for s in successors[u]:
            if s not in est or u_finish > est[s]:
                est[s] = u_finish
            in_degree[s] -= 1
            if in_degree[s] == 0:
                queue.append(s)

    makespan_ub = est.get(end_id, 0)

    # Backward pass
    lft = {}
    for u in reversed(topo_order):
        succs = successors[u]
        if not succs:
            lft[u] = makespan_ub
        else:
            lft[u] = min(lft[s] - activities[s].duration for s in succs)

    return lft


def order_by_lft(project):
    lft = _compute_lft(project)
    return _priority_toposort(project, lambda i: lft.get(i, 0))


def order_by_grpw(project):
    """Greatest Rank Positional Weight: own duration + transitive successor durations."""
    cache = {}
    activities = project.activities
    successors = project.successors

    def rpw(act_id):
        if act_id in cache:
            return cache[act_id]
        total = 0
        for s in successors[act_id]:
            total += activities[s].duration + rpw(s)
        cache[act_id] = total
        return total

    for aid in project.all_ids():
        rpw(aid)

    return _priority_toposort(project, lambda i: -(activities[i].duration + cache.get(i, 0)))


def get_all_priority_orders(project):
    """Return list of (name, activity_list) from all priority rules."""
    return [
        ("id", order_by_id(project)),
        ("spt", order_by_duration(project)),
        ("mts", order_by_successors(project)),
        ("lft", order_by_lft(project)),
        ("grpw", order_by_grpw(project)),
    ]
