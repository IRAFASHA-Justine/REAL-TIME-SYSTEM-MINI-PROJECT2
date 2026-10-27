"""Mini Project 2.2 experiments: analyse all six sets and save charts."""
import os, json
import matplotlib
matplotlib.use("Agg")
from sched_tool import SETS, analyze, compare_chart

os.makedirs("figs", exist_ok=True)
os.makedirs("results", exist_ok=True)

res = {}
for k, ts in SETS.items():
    a = analyze(ts)
    res[k] = {x: v for x, v in a.items() if x != "per_task"}
    tag = k.split()[0].lower()
    if tag in {"s1", "s2", "s4", "s6"}:
        compare_chart(ts, f"figs/cmp_{tag}.png")

json.dump(res, open("results/mp22.json", "w"), default=str)
print("ok")