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
from scheduler import ssgs, get_makespan, order_by_lft, order_by_successors, order_by_grpw


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


def _compute_lft_values(project):
    """Compute latest-finish-time values (ignoring resources) for priority guidance."""
    end_id = project.n + 1
    est = {aid: 0 for aid in project.all_ids()}

    for aid in project.all_ids():
      finish = est[aid] + project.activities[aid].duration
      for succ in project.successors[aid]:
        if finish > est[succ]:
          est[succ] = finish

    ub = est[end_id]
    lft = {aid: ub for aid in project.all_ids()}
    lft[end_id] = ub

    for aid in reversed(project.all_ids()):
      if aid == end_id:
        continue
      succs = project.successors[aid]
      if succs:
        lft[aid] = min(lft[s] - project.activities[s].duration for s in succs)
      else:
        lft[aid] = ub

    return lft


def _evaluate_order(project, activity_list):
    """Decode an activity list with SSGS and return (schedule, makespan)."""
    sched = ssgs(project, activity_list)
    return sched, get_makespan(project, sched)


def _weighted_choice(items, weights):
    """Roulette-wheel selection over named operators."""
    total = sum(max(0.0001, weights[x]) for x in items)
    roll = random.random() * total
    run = 0.0
    for item in items:
      run += max(0.0001, weights[item])
      if run >= roll:
        return item
    return items[-1]


def _precedence_ok_at_position(project, partial_order, act_id, pos):
    """Check if inserting act_id at pos keeps precedence feasible in partial_order."""
    idx = {aid: i for i, aid in enumerate(partial_order)}

    for pred in project.predecessors[act_id]:
      if pred == 0:
        continue
      if pred in idx and idx[pred] >= pos:
        return False

    for succ in project.successors[act_id]:
      if succ == project.n + 1:
        continue
      if succ in idx and idx[succ] < pos:
        return False

    return True


def _feasible_positions(project, partial_order, act_id):
    """All insertion indices that preserve precedence relative to already-placed tasks."""
    positions = []
    for pos in range(len(partial_order) + 1):
      if _precedence_ok_at_position(project, partial_order, act_id, pos):
        positions.append(pos)
    return positions


def _complete_order_from_partial(project, fixed_order, lft_values):
    """Complete a precedence-feasible full order while preserving fixed_order subsequence."""
    fixed = list(fixed_order)
    fixed_set = set(fixed)
    next_fixed = 0

    placed = {0}
    remaining = set(project.real_ids())
    full = []

    while remaining:
      fixed_target = fixed[next_fixed] if next_fixed < len(fixed) else None

      eligible = [
        aid for aid in remaining
        if all(pred in placed for pred in project.predecessors[aid])
      ]

      if not eligible:
        if fixed_target is not None and fixed_target in remaining:
          pick = fixed_target
          next_fixed += 1
        else:
          pick = random.choice(list(remaining))
      else:
        non_fixed_eligible = [aid for aid in eligible if aid not in fixed_set]
        fixed_is_eligible = fixed_target in eligible if fixed_target is not None else False

        if fixed_is_eligible and (not non_fixed_eligible or random.random() < 0.5):
          pick = fixed_target
          next_fixed += 1
        elif non_fixed_eligible:
          pick = min(
            non_fixed_eligible,
            key=lambda aid: (lft_values.get(aid, 0), project.activities[aid].duration, aid),
          )
        elif fixed_is_eligible:
          pick = fixed_target
          next_fixed += 1
        else:
          pick = random.choice(eligible)

      full.append(pick)
      placed.add(pick)
      remaining.remove(pick)

    return full


def _topological_repair(project, maybe_invalid):
    """Repair an invalid order by reconstructing a precedence-feasible topological order."""
    preferred_rank = {aid: i for i, aid in enumerate(maybe_invalid)}
    placed = {0}
    remaining = set(project.real_ids())
    out = []

    while remaining:
      eligible = [aid for aid in remaining if all(pred in placed for pred in project.predecessors[aid])]
      if not eligible:
        eligible = list(remaining)
      pick = min(eligible, key=lambda aid: preferred_rank.get(aid, project.n + aid))
      out.append(pick)
      placed.add(pick)
      remaining.remove(pick)

    return out


def _destroy_random(order, remove_count):
    removed = set(random.sample(order, min(remove_count, len(order))))
    kept = [aid for aid in order if aid not in removed]
    return kept, list(removed)


def _destroy_critical(order, remove_count, schedule, project):
    """Remove activities finishing late (near critical chain)."""
    scored = []
    for aid in order:
      start = schedule.get(aid, 0)
      finish = start + project.activities[aid].duration
      scored.append((finish, start, aid))
    scored.sort(reverse=True)
    removed = [aid for _, _, aid in scored[: min(remove_count, len(scored))]]
    removed_set = set(removed)
    kept = [aid for aid in order if aid not in removed_set]
    return kept, removed


def _destroy_resource_heavy(order, remove_count, project):
    """Remove resource-heavy activities to re-open congested regions."""
    scored = []
    for aid in order:
      act = project.activities[aid]
      demand = 0.0
      for r in range(project.k):
        cap = max(1, project.capacities[r])
        demand += act.resources[r] / cap
      score = demand * max(1, act.duration)
      scored.append((score, act.duration, aid))
    scored.sort(reverse=True)
    removed = [aid for _, _, aid in scored[: min(remove_count, len(scored))]]
    removed_set = set(removed)
    kept = [aid for aid in order if aid not in removed_set]
    return kept, removed


def _projected_cost_with_completion(project, partial_order, lft_values):
    full = _complete_order_from_partial(project, partial_order, lft_values)
    _, ms = _evaluate_order(project, full)
    return ms, full


def _repair_greedy_best(project, base_order, removed, lft_values):
    """Insert each removed activity at best currently feasible index by projected makespan."""
    partial = base_order[:]
    remaining = removed[:]
    random.shuffle(remaining)

    while remaining:
      aid = remaining.pop()
      positions = _feasible_positions(project, partial, aid)
      if not positions:
        partial.append(aid)
        partial = _topological_repair(project, partial)
        continue

      best_pos = positions[0]
      best_cost = float('inf')
      for pos in positions:
        candidate_partial = partial[:]
        candidate_partial.insert(pos, aid)
        cost, _ = _projected_cost_with_completion(project, candidate_partial, lft_values)
        if cost < best_cost:
          best_cost = cost
          best_pos = pos

      partial.insert(best_pos, aid)

    return _complete_order_from_partial(project, partial, lft_values)


def _repair_regret2(project, base_order, removed, lft_values):
    """Regret-2 insertion: prioritize activities with biggest 2nd-best minus best insertion cost."""
    partial = base_order[:]
    remaining = set(removed)

    while remaining:
      choice = None
      best_pos_for_choice = None
      best_regret = -1.0

      for aid in list(remaining):
        positions = _feasible_positions(project, partial, aid)
        if not positions:
          continue

        costs = []
        for pos in positions:
          candidate_partial = partial[:]
          candidate_partial.insert(pos, aid)
          cost, _ = _projected_cost_with_completion(project, candidate_partial, lft_values)
          costs.append((cost, pos))

        costs.sort(key=lambda x: x[0])
        best_cost, best_pos = costs[0]
        second_cost = costs[1][0] if len(costs) > 1 else best_cost
        regret = second_cost - best_cost

        if regret > best_regret:
          best_regret = regret
          choice = aid
          best_pos_for_choice = best_pos

      if choice is None:
        aid = remaining.pop()
        partial.append(aid)
        partial = _topological_repair(project, partial)
        continue

      partial.insert(best_pos_for_choice, choice)
      remaining.remove(choice)

    return _complete_order_from_partial(project, partial, lft_values)


def _repair_lft_guided(project, base_order, removed, lft_values):
    """Insert removed activities by urgency (LFT ascending) at earliest precedence-feasible index."""
    partial = base_order[:]
    for aid in sorted(removed, key=lambda x: (lft_values.get(x, 0), x)):
      positions = _feasible_positions(project, partial, aid)
      if not positions:
        partial.append(aid)
        partial = _topological_repair(project, partial)
        continue
      partial.insert(min(positions), aid)

    return _complete_order_from_partial(project, partial, lft_values)


def _local_search_improve(project, order, best_ms, deadline, tries=120):
    """Fast first-improvement local search using insertion and adjacent swap moves."""
    current = order[:]
    current_best_ms = best_ms

    for _ in range(tries):
      if time.time() >= deadline:
        break

      improved = False
      n = len(current)

      if n >= 2:
        i = random.randint(0, n - 2)
        candidate = current[:]
        candidate[i], candidate[i + 1] = candidate[i + 1], candidate[i]
        if is_precedence_feasible(project, candidate):
          _, ms = _evaluate_order(project, candidate)
          if ms < current_best_ms:
            current = candidate
            current_best_ms = ms
            improved = True

      if improved:
        continue

      if n >= 3:
        i = random.randint(0, n - 1)
        j = random.randint(0, n - 1)
        if i != j:
          candidate = current[:]
          act = candidate.pop(i)
          candidate.insert(j, act)
          if is_precedence_feasible(project, candidate):
            _, ms = _evaluate_order(project, candidate)
            if ms < current_best_ms:
              current = candidate
              current_best_ms = ms

    return current, current_best_ms


def alns_optimize(project, time_limit=25):
    """
    Adaptive Large Neighborhood Search (ALNS) with SSGS decoding.

    This is a strong single-worker optimizer for RCPSP that repeatedly:
      1) destroys part of the activity order,
      2) repairs it with one of several insertion heuristics,
      3) accepts/rejects using simulated annealing,
      4) adapts operator probabilities by observed gains.
    """
    start = time.time()
    deadline = start + time_limit

    # Initial seed: deterministic priority rules + random topological orders.
    lft_values = _compute_lft_values(project)
    seeds = [
      order_by_lft(project),
      order_by_successors(project),
      order_by_grpw(project),
    ]
    for _ in range(2):
      seeds.append(random_activity_list(project))

    best_order = None
    best_schedule = None
    best_ms = float('inf')

    for seed in seeds:
      if not is_precedence_feasible(project, seed):
        seed = _topological_repair(project, seed)
      sched, ms = _evaluate_order(project, seed)
      if ms < best_ms:
        best_ms = ms
        best_schedule = sched
        best_order = seed[:]

    current_order = best_order[:]
    current_ms = best_ms
    current_schedule = best_schedule

    destroy_ops = ["random", "critical", "resource"]
    repair_ops = ["greedy", "regret2", "lft"]
    destroy_weights = {name: 1.0 for name in destroy_ops}
    repair_weights = {name: 1.0 for name in repair_ops}
    destroy_scores = {name: 0.0 for name in destroy_ops}
    repair_scores = {name: 0.0 for name in repair_ops}
    destroy_uses = {name: 0 for name in destroy_ops}
    repair_uses = {name: 0 for name in repair_ops}

    segment_len = 25
    iteration = 0

    temperature = max(1.0, 0.08 * best_ms)
    min_temperature = 0.05
    cooling = 0.997

    n = project.n
    remove_low = max(2, int(0.20 * n))
    remove_high = max(remove_low, int(0.45 * n))

    while time.time() < deadline:
      iteration += 1

      d_name = _weighted_choice(destroy_ops, destroy_weights)
      r_name = _weighted_choice(repair_ops, repair_weights)
      destroy_uses[d_name] += 1
      repair_uses[r_name] += 1

      q = random.randint(remove_low, max(remove_low, remove_high))

      if d_name == "random":
        base_order, removed = _destroy_random(current_order, q)
      elif d_name == "critical":
        base_order, removed = _destroy_critical(current_order, q, current_schedule, project)
      else:
        base_order, removed = _destroy_resource_heavy(current_order, q, project)

      if r_name == "greedy":
        candidate_order = _repair_greedy_best(project, base_order, removed, lft_values)
      elif r_name == "regret2":
        candidate_order = _repair_regret2(project, base_order, removed, lft_values)
      else:
        candidate_order = _repair_lft_guided(project, base_order, removed, lft_values)

      if not is_precedence_feasible(project, candidate_order):
        candidate_order = _topological_repair(project, candidate_order)

      try:
        candidate_schedule, candidate_ms = _evaluate_order(project, candidate_order)
      except Exception:
        temperature = max(min_temperature, temperature * cooling)
        continue

      reward = 0.0
      delta = candidate_ms - current_ms
      accept = False

      if delta <= 0:
        accept = True
        reward = 2.0
      else:
        prob = pow(2.718281828, -delta / max(min_temperature, temperature))
        if random.random() < prob:
          accept = True
          reward = 0.5

      if accept:
        current_order = candidate_order
        current_ms = candidate_ms
        current_schedule = candidate_schedule

        if candidate_ms < best_ms:
          best_ms = candidate_ms
          best_order = candidate_order[:]
          best_schedule = candidate_schedule
          reward = 6.0

      destroy_scores[d_name] += reward
      repair_scores[r_name] += reward

      # Periodic intensification around best solution.
      if iteration % 40 == 0 and time.time() < deadline:
        ls_deadline = min(deadline, time.time() + min(0.20, 0.10 * time_limit))
        improved_order, improved_ms = _local_search_improve(project, best_order, best_ms, ls_deadline)
        if improved_ms < best_ms:
          best_order = improved_order
          best_schedule, best_ms = _evaluate_order(project, best_order)
          current_order = best_order[:]
          current_ms = best_ms
          current_schedule = best_schedule

      # Update adaptive weights every segment.
      if iteration % segment_len == 0:
        reaction = 0.35
        for name in destroy_ops:
          avg = destroy_scores[name] / max(1, destroy_uses[name])
          destroy_weights[name] = (1 - reaction) * destroy_weights[name] + reaction * max(0.1, avg)
          destroy_scores[name] = 0.0
          destroy_uses[name] = 0

        for name in repair_ops:
          avg = repair_scores[name] / max(1, repair_uses[name])
          repair_weights[name] = (1 - reaction) * repair_weights[name] + reaction * max(0.1, avg)
          repair_scores[name] = 0.0
          repair_uses[name] = 0

      temperature = max(min_temperature, temperature * cooling)

    if best_schedule is None:
      fallback = order_by_lft(project)
      best_schedule = ssgs(project, fallback)

    return best_schedule


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

    # Seed deterministic priority-rule baselines into the population.
    priority_seeds = [order_by_lft, order_by_successors, order_by_grpw]
    for i, rule_fn in enumerate(priority_seeds):
      if i >= pop_size:
        break
      try:
        seed = rule_fn(project)
        if is_precedence_feasible(project, seed):
          population[i] = seed
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
