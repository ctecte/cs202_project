"""
PERSON 2: Scheduler (SSGS + priority rules)
=============================================
this is the core scheduling engine.

main algorithm: Serial Schedule Generation Scheme (SSGS)
basically we schedule one activity at a time, in some priority order.
for each activity, we find the earliest time it can start without
violating precedence or resource constraints.

the "priority order" is given as an activity list — a permutation
of activity ids that respects precedence. the optimizer (person 3)
will try different orderings to find the best makespan.
"""

from models import Project, Activity


class ResourceTracker:
    """
    keeps track of how much resource is being used at each time step.
    when we schedule an activity, we "book" resources for its duration.
    then we can check if there's enough capacity before scheduling the next one.
    """

    def __init__(self, capacities):
        self.capacities = capacities
        self.k = len(capacities)
        # usage[t] = [amount used of R1, R2, ..., RK at time t]
        # using a dict so we don't need to preallocate — time steps are sparse
        self.usage = {}

    def is_feasible(self, activity, start_time):
        """
        check if we can schedule this activity starting at start_time
        without exceeding any resource capacity.

        need to check every time step from start_time to start_time + duration - 1
        (activity occupies resources for its full duration)
        """
        for t in range(start_time, start_time + activity.duration):
            current = self.usage.get(t)
            if current is None:
                current = [0] * self.k
            for r in range(self.k):
                if current[r] + activity.resources[r] > self.capacities[r]:
                    return False
        return True

    def book(self, activity, start_time):
        """
        record that this activity is scheduled at start_time.
        add its resource usage to every time step it occupies.
        """
        for t in range(start_time, start_time + activity.duration):
            if t not in self.usage:
                self.usage[t] = [0] * self.k
            for r in range(self.k):
                self.usage[t][r] += activity.resources[r]


def find_earliest_start(project, activity_id, schedule, tracker, max_horizon=None):
    """
    find the earliest time we can start this activity.

    step 1: compute the earliest time based on predecessors
            (for each pred: earliest >= S_pred + d_pred)

    step 2: from that time onwards, scan forward until resources
            are available for the full duration

    returns the earliest feasible start time.
    """
    activity = project.activities[activity_id]

    # step 1: precedence constraint
    earliest = 0
    for pred_id in project.predecessors[activity_id]:
        if pred_id not in schedule:
            raise ValueError(f"Predecessor {pred_id} of activity {activity_id} is not scheduled yet")
        pred = project.activities[pred_id]
        earliest = max(earliest, schedule[pred_id] + pred.duration)

    # step 2: resource constraint
    if max_horizon is None:
        max_horizon = sum(project.activities[i].duration for i in project.all_ids())

    t = earliest
    while not tracker.is_feasible(activity, t):
        t += 1
        if t > max_horizon:
            raise ValueError(
                f"No feasible start found for activity {activity_id} within horizon {max_horizon}"
            )
    return t


def ssgs(project, activity_list):
    """
    Serial Schedule Generation Scheme.

    activity_list: a list of activity ids in the order we want to schedule them.
                   must be precedence-feasible (if i must come before j,
                   then i appears earlier in the list).

    how it works:
      1. start dummy activity 0 at time 0
      2. go through activity_list one by one
      3. for each activity, find the earliest feasible start time
      4. schedule it there
      5. after all done, schedule the dummy end activity

    returns a dict: activity_id -> start_time
    """
    tracker = ResourceTracker(project.capacities)
    schedule = {}
    max_horizon = sum(project.activities[i].duration for i in project.all_ids())

    # Fail fast on impossible renewable demand to avoid infinite scans.
    for act_id in project.real_ids():
        act = project.activities[act_id]
        for r in range(project.k):
            if act.resources[r] > project.capacities[r]:
                raise ValueError(
                    f"Activity {act_id} requires R{r + 1}={act.resources[r]} > cap {project.capacities[r]}"
                )

    # schedule dummy start at time 0
    schedule[0] = 0
    tracker.book(project.activities[0], 0)

    # schedule each real activity in the given order
    for act_id in activity_list:
        if act_id < 1 or act_id > project.n:
            continue
        if act_id in schedule:
            continue
        start = find_earliest_start(project, act_id, schedule, tracker, max_horizon=max_horizon)
        schedule[act_id] = start
        tracker.book(project.activities[act_id], start)

    # schedule dummy end — its start time = the makespan
    end_id = project.n + 1
    schedule[end_id] = find_earliest_start(project, end_id, schedule, tracker, max_horizon=max_horizon)

    return schedule


def get_makespan(project, schedule):
    """just return the start time of the dummy end activity — that's the makespan."""
    return schedule.get(project.n + 1, -1)


def topological_sequential_schedule(project):
    """
    Baseline benchmark required by the project brief:
    1) build a precedence-feasible topological order,
    2) ignore resource optimization,
    3) schedule activities one-by-one sequentially.

    This produces a valid but intentionally weak baseline.
    """
    order = precedence_feasible_order(project, priority_key=lambda aid: aid)
    schedule = {0: 0}
    current_time = 0

    for act_id in order:
        act = project.activities[act_id]
        pred_ready = 0
        for pred_id in project.predecessors[act_id]:
            pred = project.activities[pred_id]
            pred_ready = max(pred_ready, schedule[pred_id] + pred.duration)

        start_time = max(current_time, pred_ready)
        schedule[act_id] = start_time
        current_time = start_time + act.duration

    end_id = project.n + 1
    end_ready = 0
    for pred_id in project.predecessors[end_id]:
        pred = project.activities[pred_id]
        end_ready = max(end_ready, schedule[pred_id] + pred.duration)
    schedule[end_id] = max(current_time, end_ready)

    return schedule


def precedence_feasible_order(project, priority_key=None):
    """
    Build a precedence-feasible activity list using topological selection.
    When multiple activities are eligible, pick by `priority_key(activity_id)` then id.
    """
    placed = {0}
    remaining = set(project.real_ids())
    order = []

    if priority_key is None:
        priority_key = lambda aid: aid

    while remaining:
        eligible = [
            aid for aid in remaining
            if all(pred in placed for pred in project.predecessors[aid])
        ]
        if not eligible:
            # Defensive fallback for malformed/cyclic input.
            eligible = list(remaining)

        pick = min(eligible, key=lambda aid: (priority_key(aid), aid))
        order.append(pick)
        placed.add(pick)
        remaining.remove(pick)

    return order


# ========================================
# PRIORITY RULES
# ========================================
# these generate the activity_list ordering for SSGS.
# person 3 (optimizer) will also generate orderings,
# but these are good starting points / baselines.

def order_by_id(project):
    """simplest ordering — just go 1, 2, 3, ..., n. not great but good for testing."""
    return precedence_feasible_order(project, priority_key=lambda aid: aid)


def order_by_duration(project):
    """
    shortest processing time first.
    TODO: sort real activities by duration (ascending)
    """
    return precedence_feasible_order(project, priority_key=lambda aid: project.activities[aid].duration)


def order_by_successors(project):
    """
    most total successors first — the idea is activities with more
    downstream dependencies are more "important" and should go first.
    TODO: count total successors (not just direct, but transitive) for each activity
          then sort descending
    """
    memo = {}

    def total_successors(aid):
        if aid in memo:
            return memo[aid]
        visited = set()
        stack = list(project.successors[aid])
        while stack:
            nxt = stack.pop()
            if nxt in visited or nxt == project.n + 1:
                continue
            visited.add(nxt)
            stack.extend(project.successors[nxt])
        memo[aid] = len(visited)
        return memo[aid]

    return precedence_feasible_order(project, priority_key=lambda aid: -total_successors(aid))


def order_by_lft(project):
    """
    latest finish time (LFT) rule — schedule activities with earlier
    deadlines first. this is one of the best known priority rules for RCPSP.

    to compute LFT:
      1. do a forward pass to get earliest start times (ignoring resources)
      2. makespan_ub = earliest start of dummy end
      3. do a backward pass from makespan_ub to get latest finish times
      4. sort activities by LFT ascending

    TODO: implement forward pass, backward pass, then sort
    """
    end_id = project.n + 1
    est = {aid: 0 for aid in project.all_ids()}

    # Forward pass on the natural topological order of these instances.
    for aid in project.all_ids():
        finish = est[aid] + project.activities[aid].duration
        for succ in project.successors[aid]:
            if finish > est[succ]:
                est[succ] = finish

    ub = est[end_id]
    lft = {aid: ub for aid in project.all_ids()}
    lft[end_id] = ub

    # Backward pass for latest finish times.
    for aid in reversed(project.all_ids()):
        if aid == end_id:
            continue
        succs = project.successors[aid]
        if succs:
            lft[aid] = min(lft[s] - project.activities[s].duration for s in succs)
        else:
            lft[aid] = ub

    return precedence_feasible_order(
        project,
        priority_key=lambda aid: (lft[aid], project.activities[aid].duration),
    )


# quick test
if __name__ == "__main__":
    from parser import parse
    import os

    path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP1.SCH")
    proj = parse(path)

    # try basic ordering
    order = order_by_id(proj)
    print(f"activity order: {order}")

    schedule = ssgs(proj, order)
    print(f"schedule: {schedule}")
    print(f"makespan: {get_makespan(proj, schedule)}")
