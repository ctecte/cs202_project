"""
PERSON 3: Optimizer (Simulated Annealing)
==========================================
searches for a good activity ordering that gives the best makespan.

key idea:
  - a "solution" is an activity list (a permutation of [1..n])
    that respects precedence
  - we feed this list into SSGS (scheduler.py) to get a schedule
  - the makespan of that schedule = our fitness score
  - we try to find the activity list that gives the lowest makespan
"""

import math
import random
import time

from scheduler import (
    ssgs,
    get_makespan,
    order_by_lft,
    order_by_duration,
    order_by_successors,
    order_by_id,
    order_by_positional_weight,
    order_by_resource_demand,
    order_by_bottleneck,
)


def is_precedence_feasible(project, activity_list):
    if len(activity_list) != project.n:
        return False
    if set(activity_list) != set(project.real_ids()):
        return False

    pos = {act: i for i, act in enumerate(activity_list)}
    end_id = project.n + 1

    for act in activity_list:
        for succ in project.successors[act]:
            if succ == end_id:
                continue
            if pos[act] >= pos[succ]:
                return False
    return True


_CACHE_MAX = 3000


def evaluate(project, activity_list, cache):
    key = tuple(activity_list)
    if key in cache:
        return cache[key]

    sched = ssgs(project, activity_list)
    ms = get_makespan(project, sched)
    if len(cache) >= _CACHE_MAX:
        # evict an arbitrary entry to cap memory; dict preserves insertion order
        cache.pop(next(iter(cache)))
    cache[key] = (sched, ms)
    return cache[key]


def random_activity_list(project):
    placed = {0}
    activity_list = []

    while len(activity_list) < project.n:
        eligible = []
        for act_id in project.real_ids():
            if act_id in placed:
                continue
            if all(pred in placed for pred in project.predecessors[act_id]):
                eligible.append(act_id)

        if not eligible:
            raise ValueError("No eligible activity found; precedence graph may be invalid")

        chosen = random.choice(eligible)
        activity_list.append(chosen)
        placed.add(chosen)

    return activity_list


def precedence_insertion_bounds(project, activity_list, act):
    reduced = [x for x in activity_list if x != act]
    position = {a: idx for idx, a in enumerate(reduced)}

    preds = [p for p in project.predecessors[act] if p != 0]
    succs = [s for s in project.successors[act] if s != project.n + 1]

    lo = 0 if not preds else max(position[p] for p in preds) + 1
    hi = len(reduced) if not succs else min(position[s] for s in succs)

    return lo, hi, reduced


def safe_insertion_move(project, activity_list):
    if len(activity_list) <= 1:
        return activity_list[:]

    act = random.choice(activity_list)
    lo, hi, reduced = precedence_insertion_bounds(project, activity_list, act)

    if lo > hi:
        return activity_list[:]

    current_reduced_idx = None
    seen = 0
    for i, x in enumerate(activity_list):
        if x == act:
            current_reduced_idx = seen
            break
        seen += 1

    possible = [idx for idx in range(lo, hi + 1)]
    if not possible:
        return activity_list[:]

    # prefer actual movement
    if current_reduced_idx in possible and len(possible) > 1:
        possible.remove(current_reduced_idx)

    new_idx = random.choice(possible)
    new_list = reduced[:]
    new_list.insert(new_idx, act)
    return new_list


def safe_adjacent_swap(project, activity_list):
    n = len(activity_list)
    if n <= 1:
        return activity_list[:]

    # try a random adjacent pair; fall back to a random scan if it's infeasible
    indices = list(range(n - 1))
    random.shuffle(indices)
    for i in indices:
        trial = activity_list[:]
        trial[i], trial[i + 1] = trial[i + 1], trial[i]
        if is_precedence_feasible(project, trial):
            return trial

    return activity_list[:]


def mutate(project, activity_list):
    # low-overhead neighborhood for short time budgets
    if random.random() < 0.8:
        return safe_insertion_move(project, activity_list)
    return safe_adjacent_swap(project, activity_list)


def seed_orders(project):
    """Keep only a compact, high-value seed set."""
    builders = [
        order_by_successors,
        order_by_lft,
        order_by_bottleneck,
        order_by_resource_demand,
        order_by_duration,
        order_by_id,
    ]

    seeds = []
    seen = set()

    for fn in builders:
        try:
            order = fn(project)
            key = tuple(order)
            if key not in seen and is_precedence_feasible(project, order):
                seeds.append(order)
                seen.add(key)
        except Exception:
            pass

    # only a couple of random seeds to avoid too much overhead
    for _ in range(2):
        try:
            order = random_activity_list(project)
            key = tuple(order)
            if key not in seen:
                seeds.append(order)
                seen.add(key)
        except Exception:
            pass

    return seeds


def optimize(project, time_limit=28):
    """
    Main optimizer. Returns best schedule found within time_limit seconds.
    Uses Simulated Annealing over the space of precedence-feasible activity lists.
    """
    random.seed(0)
    start_time = time.time()
    cache = {}

    seeds = seed_orders(project)
    if not seeds:
        return None

    best_order = None
    best_sched = None
    best_ms = float("inf")

    for order in seeds:
        try:
            sched, ms = evaluate(project, order, cache)
            if ms < best_ms:
                best_order = order[:]
                best_sched = sched
                best_ms = ms
        except Exception:
            continue

    if best_order is None:
        return None

    current_order = best_order[:]
    current_ms = best_ms

    temperature = max(2.0, project.n / 2.0)
    # scale cooling and patience to the available budget:
    # 28s budget → slow cooling (0.996), patient restarts (200)
    # 1s budget  → faster cooling (0.97), quick restarts (30)
    if time_limit >= 10:
        cooling = 0.996
        no_improve_limit = 200
    elif time_limit >= 2:
        cooling = 0.985
        no_improve_limit = 75
    else:
        cooling = 0.97
        no_improve_limit = 30
    no_improve = 0

    while time.time() - start_time < time_limit:
        neighbor = mutate(project, current_order)

        try:
            neighbor_sched, neighbor_ms = evaluate(project, neighbor, cache)
        except Exception:
            continue

        delta = neighbor_ms - current_ms

        if delta <= 0 or random.random() < math.exp(-delta / max(temperature, 1e-9)):
            current_order = neighbor
            current_ms = neighbor_ms

        if neighbor_ms < best_ms:
            best_order = neighbor[:]
            best_sched = neighbor_sched
            best_ms = neighbor_ms
            no_improve = 0
        else:
            no_improve += 1

        # occasional reset to best known order
        if no_improve >= no_improve_limit:
            current_order = best_order[:]
            current_ms = best_ms
            no_improve = 0
            temperature = max(2.0, project.n / 2.0)

        temperature *= cooling

    return best_sched


# compatibility aliases
def genetic_algorithm(project, time_limit=28):
    return optimize(project, time_limit=time_limit)


def simulated_annealing(project, time_limit=28):
    return optimize(project, time_limit=time_limit)


# quick test
if __name__ == "__main__":
    from parser import parse
    import os

    path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP1.SCH")
    proj = parse(path)

    sched = optimize(proj, time_limit=5)
    if sched:
        print(f"best makespan: {get_makespan(proj, sched)}")
        for act_id in sorted(sched):
            print(f"  activity {act_id}: start = {sched[act_id]}")
