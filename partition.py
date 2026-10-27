"""Mini Project 2.3: partitioned multiprocessor scheduling with
bin-packing heuristics (Section 2.8)."""
from rts_sim import Task, rm_bound, total_utilization


def _admissible(core, t):
    """Does task t fit on this core under the Liu & Layland admission
    test for the resulting (new) task count?"""
    n_new = len(core) + 1
    return sum(x.U for x in core) + t.U <= rm_bound(n_new) + 1e-12


def _first_fit_sorted(tasks, m):
    cores = [[] for _ in range(m)]
    unplaced = []
    for t in tasks:
        for c in cores:
            if _admissible(c, t):
                c.append(t)
                break
        else:
            unplaced.append(t)
    return cores, unplaced


def first_fit(tasks, m):
    """FF: input order, first admissible core."""
    return _first_fit_sorted(tasks, m)


def first_fit_decreasing(tasks, m):
    """FFD: sort by decreasing utilisation, then first-fit."""
    return _first_fit_sorted(sorted(tasks, key=lambda t: -t.U), m)


def best_fit_decreasing(tasks, m):
    """BFD: sort by decreasing utilisation, pick admissible core with
    the least remaining capacity."""
    tasks = sorted(tasks, key=lambda t: -t.U)
    cores = [[] for _ in range(m)]
    unplaced = []
    for t in tasks:
        candidates = [i for i, c in enumerate(cores) if _admissible(c, t)]
        if not candidates:
            unplaced.append(t)
            continue
        best = min(
            candidates,
            key=lambda i: rm_bound(len(cores[i]) + 1)
                          - sum(x.U for x in cores[i]) - t.U,
        )
        cores[best].append(t)
    return cores, unplaced


def worst_fit(tasks, m):
    """WF: pick admissible core with the most remaining capacity."""
    cores = [[] for _ in range(m)]
    unplaced = []
    for t in tasks:
        candidates = [i for i, c in enumerate(cores) if _admissible(c, t)]
        if not candidates:
            unplaced.append(t)
            continue
        best = max(
            candidates,
            key=lambda i: rm_bound(len(cores[i]) + 1)
                          - sum(x.U for x in cores[i]) - t.U,
        )
        cores[best].append(t)
    return cores, unplaced


# The name exp23.py imports:
HEURISTICS = {
    "FF": first_fit,
    "FFD": first_fit_decreasing,
    "BFD": best_fit_decreasing,
    "WF": worst_fit,
}