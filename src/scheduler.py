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
        # TODO: implement this
        # for each time t in [start_time, start_time + duration):
        #   for each resource k:
        #     current_usage = self.usage.get(t, [0]*self.k)[k]
        #     if current_usage + activity.resources[k] > self.capacities[k]:
        #       return False
        # return True
        pass

    def book(self, activity, start_time):
        """
        record that this activity is scheduled at start_time.
        add its resource usage to every time step it occupies.
        """
        # TODO: implement this
        # for each time t in [start_time, start_time + duration):
        #   if t not in self.usage, init to [0]*self.k
        #   for each resource k:
        #     self.usage[t][k] += activity.resources[k]
        pass


def find_earliest_start(project, activity_id, schedule, tracker):
    """
    find the earliest time we can start this activity.

    step 1: compute the earliest time based on predecessors
            (for each pred with lag L: earliest >= S_pred + L)

    step 2: from that time onwards, scan forward until resources
            are available for the full duration

    returns the earliest feasible start time.
    """
    activity = project.activities[activity_id]

    # step 1: precedence constraint
    # TODO: compute earliest based on all predecessors
    # earliest = 0
    # for (pred_id, lag) in project.predecessors[activity_id]:
    #     earliest = max(earliest, schedule[pred_id] + lag)

    earliest = 0  # placeholder

    # step 2: resource constraint
    # TODO: scan forward from earliest until resources are available
    # t = earliest
    # while not tracker.is_feasible(activity, t):
    #     t += 1
    # return t

    return earliest  # placeholder


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

    # TODO: schedule each activity in the given order
    # for act_id in activity_list:
    #     start = find_earliest_start(project, act_id, schedule, tracker)
    #     schedule[act_id] = start
    #     tracker.book(project.activities[act_id], start)

    # schedule dummy end — its start time = the makespan
    # TODO: find earliest start for activity n+1
    # end_id = project.n + 1
    # schedule[end_id] = find_earliest_start(project, end_id, schedule, tracker)

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
    """simplest ordering — just go 1, 2, 3, ..., n. not great but good for testing."""
    return project.real_ids()


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
    deadlines first. this is one of the best known priority rules for RCPSP.

    to compute LFT:
      1. do a forward pass to get earliest start times (ignoring resources)
      2. makespan_ub = earliest start of dummy end
      3. do a backward pass from makespan_ub to get latest finish times
      4. sort activities by LFT ascending

    TODO: implement forward pass, backward pass, then sort
    """
    # TODO: implement — this one is abit more work but it's the best priority rule
    pass


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
