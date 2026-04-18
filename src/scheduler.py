from models import Project, Activity

class ResourceTracker:
    
    # keeps track of how much resource is being used at each time step
    # when activity scheduled, subtract resources for its duration
    # then we can check if got enough capacity before scheduling the next one
    def __init__(self, capacities):
        self.capacities = capacities
        self.k = len(capacities)
        self.usage = {}

    def is_feasible(self, activity, start_time):      
        # check if we can schedule activity starting at start_time
        # without exceeding resource constraints

        # need to check every time step from start_time to start_time + duration - 1       
        for t in range(start_time, start_time + activity.duration):
            current = self.usage.get(t)
            # no activity scheduled
            if current is None:
                current = [0] * self.k
            # check if ANY of the resources are exceeded. Prevents invalid schedules
            for r in range(self.k):
                if current[r] + activity.resources[r] > self.capacities[r]:
                    return False
        return True

    def book(self, activity, start_time):
        # reserve the timeslots and resources activity will take up
        for t in range(start_time, start_time + activity.duration):
            if t not in self.usage:
                self.usage[t] = [0] * self.k
            for r in range(self.k):
                self.usage[t][r] += activity.resources[r]


def find_earliest_start(project, activity_id, schedule, tracker, max_horizon=None):
    # greedy algorithm
    activity = project.activities[activity_id]
    # check dependencies
    earliest = 0
    for pred_id in project.predecessors[activity_id]:
        if pred_id not in schedule:
            raise ValueError(f"Predecessor {pred_id} of activity {activity_id} is not scheduled yet")
        # since activities can be scheduled in parallel, ignoring resource constraints, the earliest start time is the 
        # longest dependency
        pred = project.activities[pred_id]
        earliest = max(earliest, schedule[pred_id] + pred.duration)
    
    # TIMEOUT. This is the longest the project should ever take (assuming feasible). If i get a schedule longer than max_horizon
    # something went wrong
    if max_horizon is None:
        max_horizon = sum(project.activities[i].duration for i in project.all_ids())

    t = earliest
    while not tracker.is_feasible(activity, t):
        t += 1
        if t > max_horizon: # FIXED. check feasiblity before even running any scheduler. No more invalids
            raise ValueError(
                f"No feasible start found for activity {activity_id} within horizon {max_horizon}"
            )
    return t


def check_feasibility(project):
    # Check that no activity needs more resource than the total capacity. 
    # Since got no lags in the data set, there will always be a valid ordering if it doesnt violate resouce constraints
    # Can always find a back to back schedule. 

    for act_id in project.real_ids():
        act = project.activities[act_id]
        for r in range(project.k):
            if act.resources[r] > project.capacities[r]:
                return False
    return True


# Serial Schedule Generation Scheme
def ssgs(project, activity_list):
    # activity_list: a list of activity ids in the order we want to schedule them.

    #   1. start dummy activity 0 at time 0
    #   2. go through activity_list one by one
    #   3. for each activity, find the earliest feasible start time
    #   4. schedule it there
    #   5. after all done, schedule the dummy end activity

    # returns a dict: activity_id -> start_time
    
    tracker = ResourceTracker(project.capacities)
    schedule = {}
    max_horizon = sum(project.activities[i].duration for i in project.all_ids())

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

    # dummy start time = makespan
    end_id = project.n + 1
    schedule[end_id] = find_earliest_start(project, end_id, schedule, tracker, max_horizon=max_horizon)

    return schedule


def get_makespan(project, schedule):
    # start time of dummy end activity
    return schedule.get(project.n + 1, -1)


def topological_sequential_schedule(project):
    # baseline benchmark
    # topological sort and schedule activities serially, ignore parallel and resource optimising
    
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
    # build a precedence-feasible activity list using topological selection.
    # when multiple activities are eligible, pick by priority_key(activity_id) then id.
    
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
            eligible = list(remaining)

        pick = min(eligible, key=lambda aid: (priority_key(aid), aid))
        order.append(pick)
        placed.add(pick)
        remaining.remove(pick)

    return order


# PRIORITY RULES
# these generate the activity_list ordering for SSGS
# optimizer will test different orderings, but these are our starting points

def order_by_id(project):
    # 1 2 3 4 5 ,, n
    # not used in the actual solver, kept for testing/debugging
    return precedence_feasible_order(project, priority_key=lambda aid: aid)


def order_by_duration(project):
    # shortest processing time (SPT) first
    # not used — SPT works well for single machine scheduling but doesnt account for
    # resource contention or dependency structure, so LFT/MTS/GRPW outperform it on RCPSP
    return precedence_feasible_order(project, priority_key=lambda aid: project.activities[aid].duration)


def order_by_successors(project):
    """
    most total successors first — the idea is activities with more
    downstream dependencies are more "important" and should go first.
    TODO: count total successors (not just direct, but transitive) for each activity
          then sort descending
    """
    # most total successors (MTS) ie which activity has the most people depending on it
    # this includes chain dependencies (if C needs B, and B needs A, then C needs A)
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


def order_by_grpw(project):
    # consider dependencies and duration as well. most activities that block the most work hours are scheduled first
    # if successors take more time, then we want to unlock those asap

    memo = {}

    def rpw(aid):
        if aid in memo:
            return memo[aid]
        total = 0
        for s in project.successors[aid]:
            total += project.activities[s].duration + rpw(s)
        memo[aid] = total
        return total

    for aid in project.all_ids():
        rpw(aid)
    # final weight = activity duration + total weight of all successors (including chain dependencies)
    return precedence_feasible_order(
        project,
        priority_key=lambda aid: -(project.activities[aid].duration + memo.get(aid, 0)),
    )


def order_by_lft(project):
    # latest finish time (LFT) rule 
    # schedule activities with earlier finish times first

    # forward and backward pass is done to find the slack. Those with higher slack can be prioritised later
    # we order those with lower slacks in front of those that are higher slack, so the greedy algo can pick them first
    end_id = project.n + 1
    # earliest start time
    est = {aid: 0 for aid in project.all_ids()}

    # find earliest possible start time for every task
    for aid in project.all_ids():
        # activity finish time = earliest start of activity + duration 
        finish = est[aid] + project.activities[aid].duration
        # all successors can only start when the current predecessor is done
        for succ in project.successors[aid]:
            # update start time of successors to be == earliest finish
            if finish > est[succ]:
                est[succ] = finish

    # upper bound, ie fastest theoretical time ignoring resource constraints 
    ub = est[end_id]
    # latest finish time 
    lft = {aid: ub for aid in project.all_ids()}
    lft[end_id] = ub

    # go through activities in reverse order
    for aid in reversed(project.all_ids()):
        if aid == end_id:
            continue

        # activity's LFT = min (latest start) of all successors  
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
