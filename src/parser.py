"""
PERSON 1: Parser
=================
read .SCH files and build the Project object
see OVERVIEW.md for the full format breakdown

the file has 3 parts:
  1) header line: n, K, 0, 0
  2) successor table (n+2 lines, one per activity 0..n+1)
  3) duration + resource table (n+2 lines again)
  4) last line: resource capacities
"""

import re
from models import Activity, Project


def parse(filepath):
    """
    main parse function — give it a .SCH file path, get back a Project.

    the tricky part is the successor lines. each line looks like:
        activity_id  1  num_successors  succ1  succ2  ...  [lag1]  [lag2]  ...

    stuff in brackets are the lag values. negative lag = not a real dependency,
    just skip those edges. positive/zero lag = real constraint (S_j >= S_i + L).
    """

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # strip whitespace, remove empty lines
    lines = [l.strip() for l in lines if l.strip()]

    # --- HEADER ---
    # first line: n K 0 0
    header = lines[0].split()
    n = int(header[0])
    k = int(header[1])

    total_activities = n + 2  # including dummy start (0) and end (n+1)

    # --- SUCCESSOR TABLE ---
    # next (n+2) lines, one per activity
    # TODO: parse each line to extract:
    #   - activity id
    #   - list of successors
    #   - list of lag values (the numbers inside [ ])
    #   - only keep edges where lag >= 0
    #
    # hint: you can use something like re.findall(r'\[(-?\d+)\]', line)
    #       to pull out all the bracket values
    #       then the remaining numbers (before the brackets) give you
    #       activity_id, num_modes(1), num_successors, succ1, succ2, ...

    successors = {}   # activity_id -> [(succ_id, lag), ...]
    predecessors = {}  # activity_id -> [(pred_id, lag), ...]

    # init empty lists first
    for i in range(total_activities):
        successors[i] = []
        predecessors[i] = []

    for line_idx in range(1, total_activities + 1):
        line = lines[line_idx]

        # TODO: parse this line
        # 1. extract lag values from brackets
        # 2. remove bracket portions to get the plain numbers
        # 3. plain numbers = [activity_id, 1, num_succ, succ1, succ2, ...]
        # 4. pair each successor with its lag
        # 5. if lag >= 0, add to successors and predecessors dicts
        pass

    # --- DURATION + RESOURCE TABLE ---
    # next (n+2) lines after the successor table
    # each line: activity_id  1  duration  r1  r2  ...  rK
    #
    # TODO: parse each line and create Activity objects

    activities = {}

    for line_idx in range(total_activities + 1, 2 * total_activities + 1):
        line = lines[line_idx]

        # TODO: parse this line
        # tokens = line.split()
        # activity_id = int(tokens[0])
        # duration = int(tokens[2])       # tokens[1] is always 1 (mode)
        # resources = [int(x) for x in tokens[3:]]
        # activities[activity_id] = Activity(id=activity_id, duration=duration, resources=resources)
        pass

    # --- RESOURCE CAPACITIES ---
    # last line: R1 R2 ... RK
    #
    # TODO: parse the last line
    # capacities = [int(x) for x in lines[-1].split()]

    capacities = []

    return Project(
        n=n,
        k=k,
        activities=activities,
        successors=successors,
        predecessors=predecessors,
        capacities=capacities
    )


# quick test — run this file directly to check if parsing works
if __name__ == "__main__":
    import sys
    import os

    # default to PSP1.SCH from j10 if no arg given
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
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
