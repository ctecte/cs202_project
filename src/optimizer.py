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
from scheduler import ssgs, get_makespan, order_by_lft


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
    placed = {0}
    activity_list = []

    while len(activity_list) < project.n:
      eligible = []
      for act_id in project.real_ids():
        if act_id in placed:
          continue
        all_preds_done = all(pred_id in placed for pred_id in project.predecessors[act_id])
        if all_preds_done:
          eligible.append(act_id)

      if not eligible:
        # defensive fallback for malformed precedence data
        remaining = [i for i in project.real_ids() if i not in placed]
        eligible = remaining

      pick = random.choice(eligible)
      activity_list.append(pick)
      placed.add(pick)

    return activity_list


def is_precedence_feasible(project, activity_list):
    """
    check if an activity list respects precedence —
    for every edge i->j, i must appear before j in the list.
    useful for sanity checking after crossover/mutation.
    """
    position = {act: idx for idx, act in enumerate(activity_list)}
    for act in activity_list:
      for succ_id in project.successors[act]:
        if succ_id == project.n + 1:
          continue
        if succ_id in position and position[act] >= position[succ_id]:
          return False
    return True


# ========================================
# GENETIC ALGORITHM
# ========================================

def tournament_select(population, fitnesses, tournament_size=3):
    """
    pick a few random individuals, return the best one.
    standard tournament selection — simple and works well.
    """
    if not population:
      return None
    t = min(tournament_size, len(population))
    indices = random.sample(range(len(population)), t)
    best_idx = min(indices, key=lambda i: fitnesses[i])
    return population[best_idx][:]


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
    # Precedence-preserving merge: repeatedly pick one eligible activity
    # from either parent (in parent order), defaulting to random eligible.
    placed = {0}
    remaining = set(project.real_ids())
    child = []

    while remaining:
      eligible = [
        aid for aid in remaining
        if all(pred in placed for pred in project.predecessors[aid])
      ]
      if not eligible:
        # malformed input fallback
        eligible = list(remaining)

      from_p1 = next((aid for aid in parent1 if aid in eligible), None)
      from_p2 = next((aid for aid in parent2 if aid in eligible), None)

      if from_p1 is not None and from_p2 is not None:
        pick = from_p1 if random.random() < 0.5 else from_p2
      elif from_p1 is not None:
        pick = from_p1
      elif from_p2 is not None:
        pick = from_p2
      else:
        pick = random.choice(eligible)

      child.append(pick)
      placed.add(pick)
      remaining.remove(pick)

    return child


def mutate(activity_list, project, mutation_rate=0.1):
    """
    slightly modify the activity list.

    simple approach: with some probability, swap two adjacent activities
    (only if the swap doesn't break precedence).

    TODO: implement
    """
    mutated = activity_list[:]
    for i in range(len(mutated) - 1):
      if random.random() < mutation_rate:
        mutated[i], mutated[i + 1] = mutated[i + 1], mutated[i]
        if not is_precedence_feasible(project, mutated):
          mutated[i], mutated[i + 1] = mutated[i + 1], mutated[i]
    return mutated


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
    pop_size = 40
    best_schedule = None
    best_makespan = float('inf')
    generation = 0

    # Stop early when search is flat: helpful for larger time budgets where
    # the population converges quickly and extra time brings no gain.
    min_runtime_before_stall_check = min(1.0, max(0.2, 0.10 * time_limit))
    stall_seconds = min(8.0, max(1.0, 0.25 * time_limit))
    no_improve_generations = 0
    max_no_improve_generations = max(300, 20 * project.n)
    last_improvement_time = start_time
    restart_count = 0
    max_restarts = max(1, int(time_limit // 6))

    # --- STEP 1: generate initial population ---
    population = [random_activity_list(project) for _ in range(pop_size)]

    # Seed one deterministic strong baseline into the population.
    try:
      baseline = order_by_lft(project)
      if is_precedence_feasible(project, baseline):
        population[0] = baseline
    except Exception:
      pass

    # --- STEP 2: evaluate initial population ---
    fitnesses = []
    for individual in population:
      try:
        sched = ssgs(project, individual)
        ms = get_makespan(project, sched)
      except Exception:
        ms = float('inf')
        sched = None
      fitnesses.append(ms)
      if sched is not None and ms < best_makespan:
        best_makespan = ms
        best_schedule = sched
        last_improvement_time = time.time()
        no_improve_generations = 0

    # --- STEP 3: main loop ---
    while time.time() - start_time < time_limit:
      parent1 = tournament_select(population, fitnesses)
      parent2 = tournament_select(population, fitnesses)
      if parent1 is None or parent2 is None:
        break

      child = crossover(parent1, parent2, project)
      child = mutate(child, project)

      if not is_precedence_feasible(project, child):
        continue

      try:
        child_sched = ssgs(project, child)
        child_ms = get_makespan(project, child_sched)
      except Exception:
        continue

      worst_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
      if child_ms < fitnesses[worst_idx]:
        population[worst_idx] = child
        fitnesses[worst_idx] = child_ms

      if child_ms < best_makespan:
        best_makespan = child_ms
        best_schedule = child_sched
        last_improvement_time = time.time()
        no_improve_generations = 0
      else:
        no_improve_generations += 1

      generation += 1

      elapsed = time.time() - start_time
      stalled_for = time.time() - last_improvement_time
      stalled = (
        elapsed >= min_runtime_before_stall_check
        and stalled_for >= stall_seconds
      )
      generation_stalled = no_improve_generations >= max_no_improve_generations

      if stalled or generation_stalled:
        remaining = time_limit - elapsed
        can_restart = (
          restart_count < max_restarts
          and remaining >= min_runtime_before_stall_check
        )
        if not can_restart:
          break

        # Diversification restart: refresh population to escape local optima.
        restart_count += 1
        no_improve_generations = 0
        last_improvement_time = time.time()

        population = [random_activity_list(project) for _ in range(pop_size)]
        try:
          baseline = order_by_lft(project)
          if is_precedence_feasible(project, baseline):
            population[0] = baseline
        except Exception:
          pass

        fitnesses = []
        for individual in population:
          try:
            sched = ssgs(project, individual)
            ms = get_makespan(project, sched)
          except Exception:
            ms = float('inf')
            sched = None
          fitnesses.append(ms)
          if sched is not None and ms < best_makespan:
            best_makespan = ms
            best_schedule = sched
            last_improvement_time = time.time()
            no_improve_generations = 0

    if best_schedule is None:
      # Hard fallback to guarantee we return a schedule.
      fallback = order_by_lft(project)
      best_schedule = ssgs(project, fallback)

    return best_schedule


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
