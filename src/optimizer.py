"""
Optimizer: GA + Forward-Backward Improvement for RCPSP.
Representation: activity list (precedence-feasible permutation of [1..n]).
Decoder: SSGS from scheduler.py.
"""

import random
import math
import time
from models import Project
from scheduler import ssgs, get_makespan, get_all_priority_orders


# ========================================
# HELPERS
# ========================================

def random_activity_list(project):
    """Random precedence-feasible ordering via Kahn's with random tie-breaking."""
    placed = {0}
    result = []
    n = project.n
    predecessors = project.predecessors
    successors = project.successors

    # precompute eligible set
    eligible = []
    for act_id in range(1, n + 1):
        if all(p in placed for p in predecessors[act_id]):
            eligible.append(act_id)

    while len(result) < n:
        pick = random.choice(eligible)
        result.append(pick)
        placed.add(pick)
        eligible.remove(pick)

        # add newly eligible
        for s in successors[pick]:
            if s == n + 1 or s in placed:
                continue
            if 1 <= s <= n and all(p in placed for p in predecessors[s]):
                eligible.append(s)

    return result


def _repair_order(project, activity_list):
    """Repair a broken activity list using original order as priority hint."""
    priority = {act: idx for idx, act in enumerate(activity_list)}
    placed = {0}
    result = []
    remaining = list(activity_list)
    predecessors = project.predecessors
    n = project.n

    while remaining:
        eligible = [a for a in remaining if all(p in placed for p in predecessors[a])]
        if not eligible:
            break
        eligible.sort(key=lambda x: priority.get(x, x))
        pick = eligible[0]
        result.append(pick)
        placed.add(pick)
        remaining.remove(pick)

    return result


def is_precedence_feasible(project, activity_list):
    """Check that for every edge i->j, i appears before j."""
    position = {act: idx for idx, act in enumerate(activity_list)}
    end_id = project.n + 1
    for act in activity_list:
        for succ_id in project.successors[act]:
            if succ_id == end_id:
                continue
            if succ_id in position and position[act] >= position[succ_id]:
                return False
    return True


# ========================================
# FORWARD-BACKWARD IMPROVEMENT (FBI)
# ========================================

def forward_backward_improvement(project, activity_list, max_iters=3):
    """
    FBI: run SSGS, reorder by start time, repeat.
    Returns (best_list, best_schedule, best_makespan).
    """
    best_list = activity_list[:]
    best_sched = ssgs(project, best_list)
    best_ms = get_makespan(project, best_sched)
    current_list = best_list[:]

    for _ in range(max_iters):
        sched = ssgs(project, current_list)
        ms = get_makespan(project, sched)
        if ms < best_ms:
            best_ms = ms
            best_sched = sched
            best_list = current_list[:]

        # Reorder by (start_time, finish_time) — activities scheduled earlier go first
        new_list = sorted(current_list, key=lambda a: (sched[a], sched[a] + project.activities[a].duration))

        if not is_precedence_feasible(project, new_list):
            new_list = _repair_order(project, new_list)

        if new_list == current_list:
            break
        current_list = new_list

    # One final evaluation
    sched = ssgs(project, current_list)
    ms = get_makespan(project, sched)
    if ms < best_ms:
        best_ms = ms
        best_sched = sched
        best_list = current_list[:]

    return best_list, best_sched, best_ms


# ========================================
# GENETIC ALGORITHM
# ========================================

def tournament_select(population, fitnesses, size=3):
    """Tournament selection: pick `size` random individuals, return best."""
    indices = random.sample(range(len(population)), min(size, len(population)))
    best = min(indices, key=lambda i: fitnesses[i])
    return population[best][:]


def crossover(parent1, parent2, project):
    """
    Precedence-preserving order crossover.
    Random subset of positions from parent1, fill rest from parent2 order.
    """
    n = len(parent1)
    # choose a random contiguous segment from parent1
    start = random.randint(0, n - 1)
    end = random.randint(start + 1, n)
    segment = set(parent1[start:end])

    child = [None] * n
    # place segment from parent1
    for i in range(start, end):
        child[i] = parent1[i]

    # fill remaining positions with activities from parent2, in order
    p2_order = [a for a in parent2 if a not in segment]
    j = 0
    for i in range(n):
        if child[i] is None:
            child[i] = p2_order[j]
            j += 1

    if not is_precedence_feasible(project, child):
        child = _repair_order(project, child)

    return child


def mutate_swap(activity_list, project, rate=0.2):
    """Adjacent swap mutation — swap neighbors if precedence allows."""
    result = activity_list[:]
    n = len(result)
    successors = project.successors
    for i in range(n - 1):
        if random.random() < rate:
            a, b = result[i], result[i + 1]
            # b must not be a direct successor of a
            if b not in successors[a]:
                result[i], result[i + 1] = b, a
    return result


def mutate_insert(activity_list, project):
    """Remove a random activity and reinsert at a random valid position."""
    result = activity_list[:]
    n = len(result)
    if n < 2:
        return result

    idx = random.randint(0, n - 1)
    act = result.pop(idx)

    preds = set(project.predecessors[act]) - {0}
    succs = set(project.successors[act]) - {project.n + 1}

    lo = 0
    hi = len(result)
    for i, a in enumerate(result):
        if a in preds:
            lo = max(lo, i + 1)
        if a in succs:
            hi = min(hi, i)

    if lo > hi:
        result.insert(idx, act)
        return result

    result.insert(random.randint(lo, hi), act)
    return result


def mutate_shift(activity_list, project):
    """Shift a random activity left or right by 1-3 positions if valid."""
    result = activity_list[:]
    n = len(result)
    if n < 3:
        return result

    idx = random.randint(0, n - 1)
    act = result.pop(idx)
    shift = random.choice([-3, -2, -1, 1, 2, 3])
    new_idx = max(0, min(n - 1, idx + shift))
    result.insert(new_idx, act)

    if not is_precedence_feasible(project, result):
        # revert
        result.remove(act)
        result.insert(idx, act)

    return result


def optimize(project, time_limit=28):
    """
    Main optimizer: GA with FBI enhancement.
    Returns (best_schedule, best_makespan).
    """
    start_time = time.time()
    pop_size = 80
    best_schedule = None
    best_makespan = float('inf')

    # --- Seed with priority rules ---
    population = []
    fitnesses = []

    for name, order in get_all_priority_orders(project):
        sched = ssgs(project, order)
        ms = get_makespan(project, sched)
        population.append(order)
        fitnesses.append(ms)
        if ms < best_makespan:
            best_makespan = ms
            best_schedule = sched

    # --- Apply FBI to priority rule seeds ---
    for i in range(len(population)):
        if time.time() - start_time > time_limit * 0.1:
            break
        new_list, new_sched, new_ms = forward_backward_improvement(project, population[i])
        population[i] = new_list
        fitnesses[i] = new_ms
        if new_ms < best_makespan:
            best_makespan = new_ms
            best_schedule = new_sched

    # --- Fill population with random individuals + FBI ---
    while len(population) < pop_size:
        if time.time() - start_time > time_limit * 0.2:
            # just add without FBI
            ind = random_activity_list(project)
            sched = ssgs(project, ind)
            ms = get_makespan(project, sched)
        else:
            ind = random_activity_list(project)
            ind, sched, ms = forward_backward_improvement(project, ind, max_iters=2)

        population.append(ind)
        fitnesses.append(ms)
        if ms < best_makespan:
            best_makespan = ms
            best_schedule = sched

    # --- Main GA loop ---
    generation = 0
    stale = 0
    last_best = best_makespan

    while time.time() - start_time < time_limit:
        # Select parents (tournament)
        p1 = tournament_select(population, fitnesses, size=3)
        p2 = tournament_select(population, fitnesses, size=3)

        # Crossover
        child = crossover(p1, p2, project)

        # Mutation (pick one of three operators)
        r = random.random()
        if r < 0.4:
            child = mutate_swap(child, project, rate=0.2)
        elif r < 0.7:
            child = mutate_insert(child, project)
        else:
            child = mutate_shift(child, project)

        # Evaluate
        child_sched = ssgs(project, child)
        child_ms = get_makespan(project, child_sched)

        # FBI on promising children (top 20% of population)
        sorted_fits = sorted(fitnesses)
        threshold = sorted_fits[len(sorted_fits) // 5] if len(sorted_fits) > 5 else sorted_fits[-1]
        if child_ms <= threshold and random.random() < 0.15:
            child, child_sched, child_ms = forward_backward_improvement(project, child, max_iters=2)

        # Replace worst if child is better
        worst_idx = max(range(len(population)), key=lambda i: fitnesses[i])
        if child_ms < fitnesses[worst_idx]:
            population[worst_idx] = child
            fitnesses[worst_idx] = child_ms

        if child_ms < best_makespan:
            best_makespan = child_ms
            best_schedule = child_sched
            stale = 0

        generation += 1
        stale += 1

        # Diversity injection when stuck
        if stale > 500:
            # Replace bottom 20% with fresh random individuals
            n_replace = pop_size // 5
            worst_indices = sorted(range(len(population)), key=lambda i: -fitnesses[i])[:n_replace]
            for wi in worst_indices:
                fresh = random_activity_list(project)
                fresh_sched = ssgs(project, fresh)
                fresh_ms = get_makespan(project, fresh_sched)
                population[wi] = fresh
                fitnesses[wi] = fresh_ms
                if fresh_ms < best_makespan:
                    best_makespan = fresh_ms
                    best_schedule = fresh_sched
            stale = 0

    return best_schedule, best_makespan
