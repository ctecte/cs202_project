"""
PERSON 3: Optimizer (Genetic Algorithm / Simulated Annealing)
==============================================================
this is where the magic happens — we use metaheuristics to search
for a good activity ordering that gives us the best makespan.

key idea:
  - a "solution" is an activity list (a permutation of [1..n])
    that respects precedence
  - we feed this list into SSGS (scheduler.py) to get a schedule
  - the makespan of that schedule = our fitness score
  - we try to find the activity list that gives the lowest makespan

two approaches provided below (pick one or try both):
  1. Genetic Algorithm (GA)
  2. Simulated Annealing (SA)
"""

import random
import time
from models import Project
from scheduler import ssgs, get_makespan


# ========================================
# HELPER: generating valid activity lists
# ========================================

def random_activity_list(project):
    """
    generate a random precedence-feasible activity list.

    approach: topological sort with random tie-breaking.
      1. find all activities whose predecessors are all "placed"
      2. randomly pick one, add it to the list
      3. repeat until all activities are placed

    this always produces a valid ordering — predecessors come before successors.
    """
    # TODO: implement this
    # placed = set()
    # placed.add(0)  # dummy start is already "done"
    # activity_list = []
    #
    # while len(activity_list) < project.n:
    #     eligible = []
    #     for act_id in project.real_ids():
    #         if act_id in placed:
    #             continue
    #         # check if all predecessors are placed
    #         all_preds_done = all(pred_id in placed for pred_id in project.predecessors[act_id])
    #         if all_preds_done:
    #             eligible.append(act_id)
    #
    #     pick = random.choice(eligible)
    #     activity_list.append(pick)
    #     placed.add(pick)
    #
    # return activity_list
    pass


def is_precedence_feasible(project, activity_list):
<<<<<<< Updated upstream
=======
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
>>>>>>> Stashed changes
    """
    check if an activity list respects precedence —
    for every edge i->j, i must appear before j in the list.
    useful for sanity checking after crossover/mutation.
    """
    # TODO: implement
    # position = {act: idx for idx, act in enumerate(activity_list)}
    # for act in activity_list:
    #     for succ_id in project.successors[act]:
    #         if succ_id == project.n + 1:  # skip dummy end
    #             continue
    #         if position[act] >= position[succ_id]:
    #             return False
    # return True
    pass


# ========================================
# GENETIC ALGORITHM
# ========================================

def tournament_select(population, fitnesses, tournament_size=3):
    """
    pick a few random individuals, return the best one.
    standard tournament selection — simple and works well.
    """
    # TODO: implement
    # pick `tournament_size` random indices from population
    # return the one with the best (lowest) fitness
    pass


def crossover(parent1, parent2, project):
    """
    precedence-preserving crossover.

    one way to do it:
      1. randomly pick ~half the positions from parent1
      2. keep those activities in the same positions
      3. fill in the remaining activities in the order they appear in parent2
      4. check that the result is still precedence-feasible

    or simpler: two-point crossover then repair if needed.

    TODO: implement — this is the trickiest part of the GA.
    make sure the result is always a valid precedence-feasible permutation.
    """
    # TODO: implement
    pass


def mutate(activity_list, project, mutation_rate=0.1):
    """
    slightly modify the activity list.

    simple approach: with some probability, swap two adjacent activities
    (only if the swap doesn't break precedence).

    TODO: implement
    """
    # TODO: implement
    # for i in range(len(activity_list) - 1):
    #     if random.random() < mutation_rate:
    #         # try swapping activity_list[i] and activity_list[i+1]
    #         # only do it if it doesn't violate precedence
    #         pass
    # return activity_list
    pass


def genetic_algorithm(project, time_limit=25):
    """
    main GA loop.

    params:
      project:    the parsed Project
      time_limit: how many seconds we have (leave some buffer from the 30s budget)

    overview:
      1. generate initial population of random activity lists
      2. evaluate each one with SSGS -> get makespan
      3. loop until time runs out:
         a. select parents
         b. crossover -> child
         c. mutate child
         d. evaluate child
         e. if child is better than worst in population, replace it
      4. return the best schedule found

    TODO: implement the full loop. suggested population size: 50-100.
    """
    start_time = time.time()
    pop_size = 50
    best_schedule = None
    best_makespan = float('inf')

    # --- STEP 1: generate initial population ---
    # TODO: create pop_size random activity lists
    # population = [random_activity_list(project) for _ in range(pop_size)]

    # --- STEP 2: evaluate initial population ---
    # TODO: for each individual, run SSGS and record the makespan
    # fitnesses = []
    # for individual in population:
    #     sched = ssgs(project, individual)
    #     ms = get_makespan(project, sched)
    #     fitnesses.append(ms)
    #     if ms < best_makespan:
    #         best_makespan = ms
    #         best_schedule = sched

    # --- STEP 3: main loop ---
    # TODO: keep improving until time runs out
    # generation = 0
    # while time.time() - start_time < time_limit:
    #     parent1 = tournament_select(population, fitnesses)
    #     parent2 = tournament_select(population, fitnesses)
    #     child = crossover(parent1, parent2, project)
    #     child = mutate(child, project)
    #
    #     child_sched = ssgs(project, child)
    #     child_ms = get_makespan(project, child_sched)
    #
    #     # replace worst individual if child is better
    #     worst_idx = fitnesses.index(max(fitnesses))
    #     if child_ms < fitnesses[worst_idx]:
    #         population[worst_idx] = child
    #         fitnesses[worst_idx] = child_ms
    #
    #     if child_ms < best_makespan:
    #         best_makespan = child_ms
    #         best_schedule = child_sched
    #
    #     generation += 1

<<<<<<< Updated upstream
    # print(f"GA done — {generation} generations, best makespan: {best_makespan}")
    return best_schedule
=======
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
>>>>>>> Stashed changes


# ========================================
# SIMULATED ANNEALING (alternative)
# ========================================

def simulated_annealing(project, time_limit=25):
    """
    SA is simpler to implement than GA — good fallback if GA is too complex.

    idea:
      1. start with a random activity list
      2. make a small change (swap two activities)
      3. if the new schedule is better, keep it
      4. if worse, keep it with some probability (that decreases over time)
      5. repeat until time runs out

    the "cooling schedule" controls how quickly we stop accepting worse solutions.
    start with high temperature (accept almost anything) and cool down gradually.

    TODO: implement — this is an alternative to GA, pick whichever one works better
    """
    # start_time = time.time()
    # current = random_activity_list(project)
    # current_sched = ssgs(project, current)
    # current_ms = get_makespan(project, current_sched)
    # best_schedule = current_sched
    # best_makespan = current_ms
    #
    # temperature = 10.0   # starting temp — tune this
    # cooling_rate = 0.995 # how fast to cool — tune this
    #
    # while time.time() - start_time < time_limit:
    #     # make a neighbor by swapping two random adjacent activities
    #     neighbor = current[:]
    #     i = random.randint(0, len(neighbor) - 2)
    #     neighbor[i], neighbor[i+1] = neighbor[i+1], neighbor[i]
    #
    #     if not is_precedence_feasible(project, neighbor):
    #         continue
    #
    #     neighbor_sched = ssgs(project, neighbor)
    #     neighbor_ms = get_makespan(project, neighbor_sched)
    #
    #     delta = neighbor_ms - current_ms
    #     if delta < 0 or random.random() < math.exp(-delta / temperature):
    #         current = neighbor
    #         current_ms = neighbor_ms
    #         current_sched = neighbor_sched
    #
    #     if current_ms < best_makespan:
    #         best_makespan = current_ms
    #         best_schedule = current_sched
    #
    #     temperature *= cooling_rate
    #
    # return best_schedule
    pass


# quick test
if __name__ == "__main__":
    from parser import parse
    import os

    path = os.path.join(os.path.dirname(__file__), "..", "sm_j10", "PSP1.SCH")
    proj = parse(path)

    sched = genetic_algorithm(proj, time_limit=5)
    if sched:
        print(f"best makespan: {get_makespan(proj, sched)}")
        for act_id in sorted(sched):
            print(f"  activity {act_id}: start = {sched[act_id]}")
