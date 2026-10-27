"""Mini Project 2.2: RM vs EDF schedulability comparison tool.
Usage:
    python sched_tool.py tasks.csv [chart.png]   (CSV columns: name,C,T[,D])
    python sched_tool.py --demo
"""
import csv, sys, math
from rts_sim import *


def load_csv(path):
    tasks = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            d = (r.get("D") or "").strip()
            tasks.append(Task(r["name"].strip(), int(r["C"]),
                              int(r["T"]), int(d) if d else None))
    return tasks


def validate(tasks):
    if not tasks:
        return "empty task set"
    for t in tasks:
        if t.C <= 0 or t.T <= 0 or t.D <= 0:
            return f"{t.name}: C, T and D must be positive"
        if t.D > t.T:
            return f"{t.name}: D > T (arbitrary deadlines) is not supported"
        if t.C > t.D:
            return f"{t.name}: C > D, the task can never meet its deadline"
    return None


def analyze(tasks, cap=500):
    err = validate(tasks)
    if err:
        return dict(error=err)
    constrained = any(t.D < t.T for t in tasks)
    n = len(tasks)
    U = total_utilization(tasks)
    order = priority_order(tasks, "DM" if constrained else "RM")
    out = dict(n=n, U=U, bound=rm_bound(n), constrained=constrained,
               order=[t.name for t in order],
               per_task=[(t.name, t.C, t.T, t.D, t.U) for t in tasks],
               infeasible=U > 1 + 1e-12)
    out["bound_pass"] = (not constrained) and U <= out["bound"] + 1e-12
    out["edf_pass"] = U <= 1 + 1e-12
    out["rta"] = None
    if not out["infeasible"] and not out["bound_pass"]:
        rows = []
        for i, t in enumerate(order):
            R, it, ok = rta(order, i)
            rows.append((t.name, R, it, t.D, ok))
        out["rta"] = rows
        out["rm_ok"] = all(r[4] for r in rows)
    else:
        out["rm_ok"] = out["bound_pass"]
    if out["infeasible"]:
        out["rm_ok"] = False
    H = hyperperiod(tasks)
    out["hyper"] = H
    out["horizon"] = min(H, cap)
    if not out["infeasible"]:
        out["rm_sim_misses"] = simulate(tasks, out["horizon"],
                                        "DM" if constrained else "RM")["misses"]
        out["edf_sim_misses"] = simulate(tasks, out["horizon"], "EDF")["misses"]
    return out


def report(name, tasks):
    a = analyze(tasks)
    L = [f"=== {name} ==="]
    if "error" in a:
        return "\n".join(L + [f"INPUT ERROR: {a['error']}"])
    for nm, C, T, D, u in a["per_task"]:
        L.append(f"  {nm}: C={C} T={T} D={D} u={u:.3f}")
    L.append(f"  n={a['n']} total U={a['U']:.3f} hyperperiod={a['hyper']}")
    if a["infeasible"]:
        L.append("  VERDICT: INFEASIBLE (U > 1): no scheduler can meet "
                 "all deadlines on one processor.")
        return "\n".join(L)
    if a["constrained"]:
        L.append(f"  Constrained deadlines present: Deadline Monotonic "
                 f"order {a['order']}; Liu-Layland bound not applicable, "
                 f"using RTA")
    else:
        L.append(f"  Liu-Layland bound n(2^(1/n)-1) = {a['bound']:.3f}: "
                 f"{'PASS' if a['bound_pass'] else 'FAIL (inconclusive)'}")
    if a["rta"]:
        for nm, Rv, it, D, ok in a["rta"]:
            L.append(f"  RTA {nm}: R={Rv} (iterations {it}) vs D={D}: "
                     f"{'OK' if ok else 'MISS'}")
    L.append(f"  RM/DM verdict: {'SCHEDULABLE' if a['rm_ok'] else 'NOT schedulable'}")
    L.append(f"  EDF (U <= 1): {'PASS' if a['edf_pass'] else 'FAIL'}"
             + (" (necessary only when D < T)" if a["constrained"] else ""))
    L.append(f"  simulated misses over {a['horizon']} ticks: "
             f"RM/DM={len(a['rm_sim_misses'])}, "
             f"EDF={len(a['edf_sim_misses'])}")
    return "\n".join(L)


def compare_chart(tasks, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    a = analyze(tasks)
    if "error" in a or a["infeasible"]:
        return False
    H = a["horizon"]
    pol = "DM" if a["constrained"] else "RM"
    fig, ax = plt.subplots(2, 1,
                           figsize=(7.2, 1.2 + 0.55 * len(tasks) * 2),
                           sharex=True)
    draw_schedule(ax[0], tasks, simulate(tasks, H, pol),
                  f"{pol} (hyperperiod {a['hyper']})", H)
    draw_schedule(ax[1], tasks, simulate(tasks, H, "EDF"), "EDF", H)
    ax[1].set_xlabel("time (ticks)")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return True


SETS = {
    "S1 Section 2.2.2 (3 tasks)":
        [Task("t1", 1, 4), Task("t2", 2, 6), Task("t3", 2, 12)],
    "S2 Section 2.3.2 (4 tasks)":
        [Task("t1", 1, 4), Task("t2", 2, 6), Task("t3", 2, 12), Task("t4", 1, 8)],
    "S3 overloaded (U > 1)":
        [Task("a", 3, 5), Task("b", 4, 6), Task("c", 1, 4)],
    "S4 constrained deadline":
        [Task("a", 2, 6), Task("b", 2, 8, 3), Task("c", 1, 12)],
    "S5 eight tasks, U = 0.70": [
        Task(f"t{i+1}", c, p) for i, (c, p) in enumerate(
            [(1, 10), (2, 20), (2, 20), (3, 40), (3, 40),
             (4, 40), (6, 80), (6, 80)])],
    "S6 eight harmonic tasks, U = 0.80": [
        Task(f"t{i+1}", c, p) for i, (c, p) in enumerate(
            [(1, 10), (2, 20), (2, 20), (4, 40), (4, 40),
             (4, 40), (8, 80), (8, 80)])],
}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--demo":
        ts = load_csv(sys.argv[1])
        print(report(sys.argv[1], ts))
        if len(sys.argv) > 2:
            ok = compare_chart(ts, sys.argv[2])
            print("chart written" if ok else "no chart (invalid or infeasible set)")
    else:
        for k, v in SETS.items():
            print(report(k, v))
            print()