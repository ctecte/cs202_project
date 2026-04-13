from models import Activity, Project
import sys
import os


def _would_create_cycle(predecessors, node, new_pred):
    """
    Check if adding new_pred as a predecessor of node would create a cycle.
    Traverses existing predecessors from node; if we can reach new_pred, it's a cycle.
    """
    visited = set()
    stack = [node]
    while stack:
        curr = stack.pop()
        if curr == new_pred:
            return True
        if curr in visited:
            continue
        visited.add(curr)
        for pred in predecessors.get(curr, []):
            stack.append(pred)
    return False


def parse(filepath):
    # Format: ProGenMax RCPSP/max
    # successor line: activity_id  mode  num_successors  succ1  succ2  ...  [lag1]  [lag2]  ...
    # resource line:  activity_id  mode  duration  r1  r2  ...  rK
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # remove whitespace and empty lines
    lines = [l.strip() for l in lines if l.strip()]

    header = lines[0].split()
    n = int(header[0])
    k = int(header[1])

    # j10 format: "n k"  (no mode column in data lines)
    # j20 format: "n k 0 0"  (has a mode column in every data line)
    has_mode = len(header) > 2

    total_activities = n + 2  # including dummy start and end

    successors = {}
    predecessors = {}

    for i in range(total_activities):
        successors[i] = []
        predecessors[i] = []

    for line_idx in range(1, total_activities + 1):
        line = lines[line_idx]

        raw_tokens = line.split()

        # extract lag values from bracketed tokens e.g. [0], [-22], [5]
        lag_values = []
        for t in raw_tokens:
            if t.startswith('[') and t.endswith(']'):
                lag_values.append(int(t[1:-1]))

        # j10: activity_id  num_successors  succ1  succ2  ...
        # j20: activity_id  mode  num_successors  succ1  succ2  ...
        tokens = [t for t in raw_tokens if not t.startswith('[')]
        activity_id = int(tokens[0])
        col = 2 if has_mode else 1  # skip mode column if present
        num_succ = int(tokens[col])

        succs = []
        for j in range(num_succ):
            succs.append(int(tokens[col + 1 + j]))

        successors[activity_id] = succs

        for j, s in enumerate(succs):
            lag = lag_values[j] if j < len(lag_values) else 0
            # only treat as a precedence constraint if lag >= 0 (forward constraint).
            # negative lags are maximal time lag (upper bound) constraints and must
            # not be added as predecessors or they create false cycles.
            # also skip if adding this edge would create a cycle — mutual zero-lag
            # edges (i->j and j->i) represent simultaneous-start in RCPSP/max.
            if lag >= 0 and not _would_create_cycle(predecessors, s, activity_id):
                predecessors[s].append(activity_id)

    activities = {}

    for line_idx in range(total_activities + 1, 2 * total_activities + 1):
        line = lines[line_idx]

        # j10: activity_id  duration  r1  r2  ...
        # j20: activity_id  mode  duration  r1  r2  ...
        tokens = [t for t in line.split() if not t.startswith('[')]
        activity_id = int(tokens[0])
        dur_col = 2 if has_mode else 1
        duration = int(tokens[dur_col])

        resources = []
        for val in tokens[dur_col + 1:]:
            resources.append(int(val))

        activities[activity_id] = Activity(id=activity_id, duration=duration, resources=resources)

    # last line is resource capacities
    cap_tokens = lines[-1].split()
    capacities = [int(c) for c in cap_tokens]

    return Project(
        n=n,
        k=k,
        activities=activities,
        successors=successors,
        predecessors=predecessors,
        capacities=capacities
    )


# test
if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP1.SCH")
    proj = parse(path)

    print(f"activities: {proj.n}, resource types: {proj.k}")
    print(f"capacities: {proj.capacities}")
    print()

    for aid in proj.all_ids():
        act = proj.activities[aid]
        succs = proj.successors[aid]
        preds = proj.predecessors[aid]
        print(f"activity {aid}: dur={act.duration}, res={act.resources}")
        print(f"  successors: {succs}")
        print(f"  predecessors: {preds}")
        print()
