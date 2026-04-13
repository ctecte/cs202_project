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
            usage_at_t = self.usage.get(t, [0] * self.k)
            for k in range(self.k):
                if usage_at_t[k] + activity.resources[k] > self.capacities[k]:
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
            for k in range(self.k):
                self.usage[t][k] += activity.resources[k]


def find_earliest_start(project, activity_id, schedule, tracker):
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
        pred = project.activities[pred_id]
        earliest = max(earliest, schedule[pred_id] + pred.duration)

    # step 2: resource constraint
    t = earliest
    max_iterations = 2000  # prevent infinite loops on over-constrained activities
    iterations = 0
    while not tracker.is_feasible(activity, t) and iterations < max_iterations:
        t += 1
        iterations += 1

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

    # schedule dummy start at time 0
    schedule[0] = 0
    tracker.book(project.activities[0], 0)

    # schedule each activity in the given order
    for act_id in activity_list:
        start = find_earliest_start(project, act_id, schedule, tracker)
        schedule[act_id] = start
        tracker.book(project.activities[act_id], start)

    # schedule dummy end — its start time = the makespan
    end_id = project.n + 1
    schedule[end_id] = find_earliest_start(project, end_id, schedule, tracker)

    return schedule


def get_makespan(project, schedule):
    """just return the start time of the dummy end activity — that's the makespan."""
    return schedule.get(project.n + 1, -1)


# ========================================
# PRIORITY RULES
# ========================================
# these generate the activity_list ordering for SSGS.
# person 3 (optimizer) will also generate orderings,
# but these are good starting points / baselines.

def order_by_id(project):
    """
    Simple ordering that respects precedence — topological sort by ID.
    Goes 1, 2, 3, ..., n but only if they respect precedence.
    """
    placed = set()
    placed.add(0)  # dummy start
    result = []

    while len(result) < project.n:
        for act_id in range(1, project.n + 1):
            if act_id in placed:
                continue
            # check if all predecessors are placed
            all_preds_done = all(pred_id in placed for pred_id in project.predecessors[act_id])
            if all_preds_done:
                result.append(act_id)
                placed.add(act_id)
                break

    return result


def order_by_duration(project):
    """
    shortest processing time first.
    TODO: sort real activities by duration (ascending)
    """
    # TODO: implement
    pass


def order_by_successors(project):
    """
    most total successors first — the idea is activities with more
    downstream dependencies are more "important" and should go first.
    TODO: count total successors (not just direct, but transitive) for each activity
          then sort descending
    """
    # TODO: implement
    pass


def order_by_lft(project):
    """
    latest finish time (LFT) rule — schedule activities with earlier
    deadlines first. one of the best known priority rules for RCPSP.

    algorithm:
      1. forward pass: compute earliest start (EST) for all activities
      2. get project makespan (EST of dummy end)
      3. backward pass: compute latest finish (LFT) from end
      4. sort activities by LFT ascending
    """
    # forward pass: compute EST (ignoring resources, just precedence)
    est = {0: 0}  # dummy start at time 0
    for act_id in range(1, project.n + 2):
        earliest = 0
        for pred_id in project.predecessors[act_id]:
            pred = project.activities[pred_id]
            earliest = max(earliest, est.get(pred_id, 0) + pred.duration)
        est[act_id] = earliest

    # project makespan = EST of dummy end
    project_makespan = est[project.n + 1]

    # backward pass: compute LFT
    lft = {project.n + 1: project_makespan}  # dummy end finishes at makespan
    for act_id in range(project.n, 0, -1):  # go backward (excluding dummy start/end)
        activity = project.activities[act_id]
        # LFT = min(LFT of successors) - duration
        latest_finish = project_makespan
        for succ_id in project.successors[act_id]:
            latest_finish = min(latest_finish, lft.get(succ_id, project_makespan) - project.activities[succ_id].duration)
        lft[act_id] = latest_finish

    # sort by LFT ascending, then by ID for tie-breaking
    placed = {0}
    result = []

    while len(result) < project.n:
        # find schedulable activity with smallest LFT among unplaced
        best = None
        best_lft = float('inf')
        for act_id in range(1, project.n + 1):
            if act_id in placed:
                continue
            # check if all predecessors are placed
            all_preds_done = all(pred_id in placed for pred_id in project.predecessors[act_id])
            if all_preds_done and lft.get(act_id, float('inf')) < best_lft:
                best = act_id
                best_lft = lft.get(act_id, float('inf'))

        if best is not None:
            result.append(best)
            placed.add(best)
        else:
            break  # shouldn't happen if project is valid

    return result


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
