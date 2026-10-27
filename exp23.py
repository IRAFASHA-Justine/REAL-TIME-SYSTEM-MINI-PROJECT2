"""Mini Project 2.3 experiments: pack five sets on m=4 cores under
FF, FFD, BFD, WF; chart + per-core RM Gantt for the FFD partition of S5."""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rts_sim import Task, rm_bound, hyperperiod, simulate, draw_schedule
from partition import HEURISTICS

os.makedirs("figs", exist_ok=True)
os.makedirs("results", exist_ok=True)

M = 4

def u(c): return sum(t.U for t in c)

TEST_SETS = {
    "S1 balanced": [Task(f"a{i}", c, p) for i, (c, p) in enumerate(
        [(3, 20), (3, 20), (3, 20), (3, 20),
         (7, 40), (7, 40), (7, 40), (7, 40),
         (2, 20), (2, 20), (2, 20), (2, 20),
         (4, 20), (4, 20), (4, 20), (4, 20)])],
    "S2 skewed": [Task(f"s{i}", 1, 10) for i in range(10)]
                 + [Task("b1", 6, 10), Task("b2", 6, 10), Task("b3", 6, 10)],
    "S3 tight": [Task(f"t{i}", 18, 100) for i in range(16)],
    "S4 adversarial": [Task(f"x{i}", 51, 100) for i in range(5)],
    "S5 mixed": [Task("m1", 2, 10), Task("m2", 3, 10),
                 Task("m3", 4, 20), Task("m4", 5, 20),
                 Task("m5", 6, 20), Task("m6", 7, 40),
                 Task("m7", 8, 40), Task("m8", 9, 40),
                 Task("m9", 10, 100), Task("m10", 11, 100)],
}

# --- heuristic comparison table ---
table = {}
for name, ts in TEST_SETS.items():
    row = {}
    for hname, fn in HEURISTICS.items():
        cores, unplaced = fn(ts, M)
        used = sum(1 for c in cores if c)
        placed = sum(u(c) for c in cores) / M * 100
        if unplaced:
            row[hname] = f"FAIL ({len(unplaced)} unplaced), {placed:.1f}%"
        else:
            row[hname] = f"{used} cores, {placed:.1f}%"
    table[name] = row
    print(name, row)

# --- bar chart of placed utilisation ---
fig, ax = plt.subplots(figsize=(7.2, 3.2))
width = 0.2
xs = list(range(len(TEST_SETS)))
for j, hname in enumerate(HEURISTICS):
    vals = []
    for name, ts in TEST_SETS.items():
        cores, unplaced = HEURISTICS[hname](ts, M)
        vals.append(sum(u(c) for c in cores) / M * 100)
    ax.bar([x + (j - 1.5) * width for x in xs], vals, width, label=hname)
ax.set_xticks(xs, list(TEST_SETS.keys()), rotation=15)
ax.set_ylabel("placed utilization (% of m = 4)")
ax.set_title("Placed utilization per heuristic (red x = some tasks could not be placed)")
ax.legend()
ax.grid(axis="y", alpha=.3)
for name, ts in TEST_SETS.items():
    for j, hname in enumerate(HEURISTICS):
        _, unplaced = HEURISTICS[hname](ts, M)
        if unplaced:
            ax.text(list(TEST_SETS).index(name) + (j - 1.5) * width, 1,
                    "x", ha="center", color="red", fontweight="bold")
plt.tight_layout()
plt.savefig("figs/packing.png", dpi=160)
plt.close()

# --- per-core RM Gantt for FFD partition of S5 ---
cores, unplaced = HEURISTICS["FFD"](TEST_SETS["S5 mixed"], M)
used_cores = [c for c in cores if c]
H = hyperperiod([t for c in used_cores for t in c])

fig, axs = plt.subplots(len(used_cores), 1, figsize=(7.2, 6.2),
                        sharex=True,
                        gridspec_kw=dict(
                            height_ratios=[max(1, len(c)) + .6
                                           for c in used_cores]))
misses = {}
for i, c in enumerate(used_cores):
    res = simulate(c, H, "RM")
    misses[f"core {i+1}"] = len(res["misses"])
    draw_schedule(axs[i], c, res,
                  f"Core {i+1}: {len(c)} tasks, U = {u(c):.3f} "
                  f"(RM bound {rm_bound(len(c)):.3f}), "
                  f"deadline misses = {len(res['misses'])}", H)
axs[-1].set_xlabel("time (ticks)")
plt.tight_layout()
plt.savefig("figs/percore.png", dpi=160)
plt.close()

json.dump(dict(
    misses=misses,
    cores=[[[t.name, t.C, t.T] for t in c] for c in used_cores],
    hyper=H,
    table=table), open("results/mp23.json", "w"), indent=2)
print("per-core misses:", misses)