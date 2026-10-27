"""Mini Project 2.1 experiments: schedules, RTA, inversion/PIP, lab tasks."""
import os, json, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rts_sim import *

os.makedirs("figs", exist_ok=True)
os.makedirs("results", exist_ok=True)
plt.rcParams.update({"font.size": 8})

R = {}
A = [Task("t1", 1, 4), Task("t2", 2, 6), Task("t3", 2, 12)]
B = A + [Task("t4", 1, 8)]
H = hyperperiod(B)

rm = simulate(B, H, "RM")
edf = simulate(B, H, "EDF")
R["hyper"] = H
R["rm_misses"] = rm["misses"]
R["edf_misses"] = edf["misses"]
R["rm_tl"] = rm["time"]
R["edf_tl"] = edf["time"]
R["diff_ticks"] = [t for t in range(H) if rm["time"][t] != edf["time"][t]]

o = priority_order(B)
R["rta"] = [(k.name, *rta(o, i)) for i, k in enumerate(o)]
R["u3"], R["b3"] = total_utilization(A), rm_bound(3)
R["u4"], R["b4"] = total_utilization(B), rm_bound(4)

# --- RM / EDF stacked chart ---
fig, ax = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True)
draw_schedule(ax[0], B, rm, "Rate Monotonic (hyperperiod 24)", H)
draw_schedule(ax[1], B, edf, "Earliest Deadline First", H)
ax[1].set_xlabel("time (ticks)")
plt.tight_layout()
plt.savefig("figs/rm_edf.png", dpi=160)
plt.close()

for nm, res in (("rm", rm), ("edf", edf)):
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    draw_schedule(ax, B, res, nm.upper(), H)
    ax.set_xlabel("time (ticks)")
    plt.tight_layout()
    plt.savefig(f"figs/gantt_{nm}.png", dpi=160)
    plt.close()

# --- priority inversion ---
none = simulate_inversion(INV_JOBS, 16, pip=False)
pip = simulate_inversion(INV_JOBS, 16, pip=True)
R["inv"] = {k: dict(finish=v["finish"], wait=v["waiting"],
                    tl=[n for n, _ in v["timeline"]])
            for k, v in (("none", none), ("pip", pip))}

fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.6), sharex=True)
draw_inversion(ax[0], none, "No protocol (unbounded inversion)", 16)
draw_inversion(ax[1], pip, "Priority Inheritance Protocol", 16)
plt.tight_layout()
plt.savefig("figs/inversion.png", dpi=160)
plt.close()

for nm, res in (("none", none), ("pip", pip)):
    fig, ax = plt.subplots(figsize=(5.2, 2.4))
    draw_inversion(ax, res, "no protocol" if nm == "none" else "PIP", 16)
    plt.tight_layout()
    plt.savefig(f"figs/inversion_{nm}.png", dpi=160)
    plt.close()

# --- Lab 1: DM vs RM ---
imp = [Task("a", 2, 6), Task("b", 2, 8)]
con = [Task("a", 2, 6), Task("b", 2, 8, 3)]

def cmpt(s):
    h = hyperperiod(s)
    r = simulate(s, h, "RM")
    d = simulate(s, h, "DM")
    return dict(same=r["time"] == d["time"],
                rm_miss=r["misses"], dm_miss=d["misses"],
                rm=r["time"], dm=d["time"])

R["dm_implicit"] = cmpt(imp)
R["dm_constrained"] = cmpt(con)

ts = con
h = hyperperiod(ts)
fig, ax = plt.subplots(2, 1, figsize=(6.4, 3.4), sharex=True)
draw_schedule(ax[0], ts, simulate(ts, h, "RM"),
              "RM priorities (D ignored): task b misses D = 3", h)
draw_schedule(ax[1], ts, simulate(ts, h, "DM"),
              "Deadline Monotonic: all deadlines met", h)
plt.tight_layout()
plt.savefig("figs/dm.png", dpi=160)
plt.close()

# --- Lab 2: bound sweep ---
ns = list(range(1, 11))
bs = [rm_bound(n) for n in ns]
R["bounds"] = bs
fig, ax = plt.subplots(figsize=(5.6, 2.6))
ax.plot(ns, bs, "o-", label="RM bound n(2^(1/n)-1)")
ax.axhline(1, color="g", ls="--", label="EDF bound = 1.0")
ax.axhline(math.log(2), color="r", ls="--", label="ln 2 = 0.693")
ax.set_xlabel("number of tasks n")
ax.set_ylabel("utilization bound")
ax.set_ylim(0.6, 1.05)
ax.legend()
ax.grid(alpha=.3)
plt.tight_layout()
plt.savefig("figs/bounds.png", dpi=160)
plt.close()

# --- Lab 3: LLF ---
R["switches"] = {p: simulate(B, H, p)["switches"] for p in ("RM", "EDF", "LLF")}
R["llf_misses"] = simulate(B, H, "LLF")["misses"]
ts2 = [Task("x", 3, 8), Task("y", 3, 8), Task("z", 2, 8)]
R["switches2"] = {p: simulate(ts2, 8, p)["switches"] for p in ("RM", "EDF", "LLF")}

fig, ax = plt.subplots(figsize=(7.2, 2.4))
draw_schedule(ax, B, simulate(B, H, "LLF"), "LLF over the hyperperiod", H)
ax.set_xlabel("time (ticks)")
plt.tight_layout()
plt.savefig("figs/llf.png", dpi=160)
plt.close()

# --- Lab 4: second medium task ---
jobs4 = INV_JOBS + [dict(name="M2", pro=2, arrive=4, C=3, res=False)]
n4 = simulate_inversion(jobs4, 20, False)
p4 = simulate_inversion(jobs4, 20, True)
R["lab4"] = dict(wait_none=n4["waiting"]["H"],
                 wait_pip=p4["waiting"]["H"],
                 fin_none=n4["finish"]["H"],
                 fin_pip=p4["finish"]["H"])

json.dump(R, open("results/mp21.json", "w"))
print("Inversion finish:", R["inv"]["none"]["finish"], R["inv"]["pip"]["finish"])
print("Inversion wait:", R["inv"]["none"]["wait"], R["inv"]["pip"]["wait"])
print("Lab4:", R["lab4"])
print("Switches:", R["switches"], "Switches2:", R["switches2"], "LLF misses:", R["llf_misses"])
print("DM implicit same:", R["dm_implicit"]["same"],
      "DM constrained same:", R["dm_constrained"]["same"],
      "RM miss:", len(R["dm_constrained"]["rm_miss"]),
      "DM miss:", len(R["dm_constrained"]["dm_miss"]))
print("RM/EDF misses:", len(R["rm_misses"]), len(R["edf_misses"]))
print("Diff ticks:", R["diff_ticks"])