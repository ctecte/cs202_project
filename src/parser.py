from models import Activity, Project
import sys
import os

def parse(filepath):

    # successor line: activity_id  num_successors  succ1  succ2  ...
    # resource line:  activity_id  duration  r1  r2  ...  rK
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # remove whitespace and empty lines
    lines = [l.strip() for l in lines if l.strip()]

    header = lines[0].split()
    n = int(header[0])
    k = int(header[1])

    total_activities = n + 2  # including dummy start and end 

    # dependencies

    # need to do sucessor first
    successors = {}    # activity_id -> [succ_id, ...]
    predecessors = {}  # activity_id -> [pred_id, ...]

    for i in range(total_activities):
        successors[i] = []
        predecessors[i] = []

    for line_idx in range(1, total_activities + 1):
        line = lines[line_idx]

        # split line into numbers and grab what we need
        tokens = line.split()
        activity_id = int(tokens[0])
        num_succ = int(tokens[1])

        succs = []
        for j in range(num_succ):
            succs.append(int(tokens[2 + j]))

        successors[activity_id] = succs

        # predecessors
        # if activity 0 -> 3, then 3 has depencency 0
        for s in succs:
            predecessors[s].append(activity_id)



    activities = {}

    for line_idx in range(total_activities + 1, 2 * total_activities + 1):
        line = lines[line_idx]

        tokens = line.split()
        activity_id = int(tokens[0])
        duration = int(tokens[1])

        # rest of the tokens are how much of each resource this activity eats up
        resources = []
        for val in tokens[2:]:
            resources.append(int(val))

        activities[activity_id] = Activity(id=activity_id, duration=duration, resources=resources)

    # last line is just the max capacity for each resource type
    # took me a while to figure out this was at the very end lol
    cap_tokens = lines[-1].split()
    capacities = []
    for c in cap_tokens:
        capacities.append(int(c))

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
    # path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP1.SCH")
    # path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP2.SCH")
    # path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP3.SCH")   
    path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP4.SCH")  
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
