"""
Mini Project 2.1: RM / DM / EDF / LLF tick simulator, RTA,
and priority inversion with PIP (Unit 2).
"""
import math
from dataclasses import dataclass
from functools import reduce


@dataclass
class Task:
    name: str
    C: int
    T: int
    D: int = None  # relative deadline, default D = T (implicit)

    def __post_init__(self):
        if self.D is None:
            self.D = self.T

    @property
    def U(self):
        return self.C / self.T


def total_utilization(tasks):
    return sum(t.U for t in tasks)


def rm_bound(n):
    """Liu & Layland bound, Section 2.2.1."""
    return n * (2 ** (1 / n) - 1)


def hyperperiod(tasks):
    return reduce(lambda a, b: a * b // math.gcd(a, b), (t.T for t in tasks))


def priority_order(tasks, policy="RM"):
    """Static priority order, highest first (RM by period, DM by deadline)."""
    key = (lambda t: t.T) if policy == "RM" else (lambda t: t.D)
    return sorted(tasks, key=key)  # stable: ties keep input order


def rta(ordered, i):
    """Response Time Analysis (Section 2.5.2) for ordered[i].
    Returns (R, iterations, meets_deadline)."""
    C = ordered[i].C
    R = ordered[i].C
    it = 0
    while True:
        it += 1
        new = C + sum(math.ceil(R / h.T) * h.C for h in ordered[:i])
        if new == R:
            return R, it, R <= ordered[i].D
        if new > ordered[i].D:
            return new, it, False
        R = new


def simulate(tasks, sim_time, policy="RM"):
    """Tick-by-tick simulation, unit time steps.
    policy in {'RM','DM','EDF','LLF'}.
    Returns dict(time=[task name or None per tick],
                misses=[...], switches=int)."""
    jobs = []
    timeline = []
    running = None
    for t in range(sim_time):
        for i, k in enumerate(tasks):
            if t % k.T == 0:
                jobs.append(dict(task=k, idx=i, rem=k.C,
                                 dt=t + k.D, rel=t,
                                 id=(k.name, t // k.T), fin=None))
        ready = [j for j in jobs if j["rem"] > 0]
        if not ready:
            timeline.append(None)
            running = None
            continue

        def key(j):
            p = {"RM": j["task"].T,
                 "DM": j["task"].D,
                 "EDF": j["dt"],
                 "LLF": j["dt"] - t - j["rem"]}[policy]
            # ties: keep the running job, then input order
            return (p, 0 if j is running else 1, j["idx"])

        cur = min(ready, key=key)
        cur["rem"] -= 1
        running = cur
        timeline.append(cur["task"].name)
        if cur["rem"] == 0:
            cur["fin"] = t + 1

    misses = [(j["id"], j["dt"], j["fin"]) for j in jobs
              if (j["fin"] is None and j["dt"] <= sim_time)
              or (j["fin"] is not None and j["fin"] > j["dt"])]
    return dict(time=timeline, misses=misses,
                switches=count_switches(tasks, sim_time, policy))


def count_switches(tasks, sim_time, policy):
    jobs, running, prev, sw = [], None, None, 0
    for t in range(sim_time):
        for i, k in enumerate(tasks):
            if t % k.T == 0:
                jobs.append(dict(task=k, idx=i, rem=k.C, dt=t + k.D))
        ready = [j for j in jobs if j["rem"] > 0]
        if not ready:
            running = None
            prev = None
            continue

        def key(j):
            p = {"RM": j["task"].T,
                 "DM": j["task"].D,
                 "EDF": j["dt"],
                 "LLF": j["dt"] - t - j["rem"]}[policy]
            return (p, 0 if j is running else 1, j["idx"])

        cur = min(ready, key=key)
        cur["rem"] -= 1
        running = cur
        if prev is not None and cur is not prev:
            sw += 1
        prev = cur
    return sw


def simulate_rm(tasks, sim_time):
    return simulate(tasks, sim_time, "RM")


def simulate_edf(tasks, sim_time):
    return simulate(tasks, sim_time, "EDF")


# ---------- priority inversion / PIP (Sections 2.6, 2.7) ----------
def simulate_inversion(jobs, sim_time, pip):
    """jobs: dicts(name, pro (bigger = higher), arrive, C, res).
    A job with res=True needs the single shared resource for its whole
    execution; it acquires it the first time it runs and releases it on
    completion."""
    st = {j["name"]: dict(j, rem=j["C"], fin=None) for j in jobs}
    holder = None
    timeline = []
    blocked_ticks = {n: 0 for n in st}

    for t in range(sim_time):
        ready = [s for s in st.values()
                 if s["arrive"] <= t and s["rem"] > 0]
        eff = {s["name"]: s["pro"] for s in ready}
        blocked = [s for s in ready
                   if s["res"] and holder is not None and holder != s["name"]]
        if pip:
            for b in blocked:
                eff[holder] = max(eff[holder], eff[b["name"]])
        runnable = [s for s in ready if s not in blocked]
        if not runnable:
            timeline.append((None, []))
            continue
        cur = max(runnable, key=lambda s: (eff[s["name"]], -s["arrive"]))
        if cur["res"] and holder is None:
            holder = cur["name"]
        cur["rem"] -= 1
        for s in ready:
            if s is not cur:
                blocked_ticks[s["name"]] += 1
        timeline.append((cur["name"], [b["name"] for b in blocked]))
        if cur["rem"] == 0:
            cur["fin"] = t + 1
            if holder == cur["name"]:
                holder = None

    return dict(timeline=timeline,
                finish={n: s["fin"] for n, s in st.items()},
                waiting=blocked_ticks)


INV_JOBS = [dict(name="L", pro=1, arrive=0, C=6, res=True),
            dict(name="H", pro=3, arrive=1, C=2, res=True),
            dict(name="M", pro=2, arrive=2, C=4, res=False)]


# ---------- plotting ----------
def _segments(timeline, names):
    segs = {n: [] for n in names}
    for t, n in enumerate(timeline):
        if n is None:
            continue
        if segs[n] and segs[n][-1][0] + segs[n][-1][1] == t:
            segs[n][-1] = (segs[n][-1][0], segs[n][-1][1] + 1)
        else:
            segs[n].append((t, 1))
    return segs


def draw_schedule(ax, tasks, res, title, horizon, show_idle=True):
    import matplotlib.pyplot as plt
    cols = plt.get_cmap("tab10")
    names = [t.name for t in tasks]
    segs = _segments(res["time"], names)
    for i, n in enumerate(names):
        ax.broken_barh(segs[n], (i - .35, .7),
                       facecolors=cols(i), edgecolor="white", linewidth=.5)
    rows = len(names)
    if show_idle:
        idle = [(t, 1) for t, n in enumerate(res["time"]) if n is None]
        ax.broken_barh(idle, (rows - .35, .7),
                       facecolors="#dddddd", hatch="//",
                       edgecolor="#999999", linewidth=.3)
        ax.set_yticks(range(rows + 1), names + ["idle"])
    else:
        ax.set_yticks(range(rows), names)
    for i, k in enumerate(tasks):  # release markers
        for r in range(0, horizon, k.T):
            ax.plot([r, r], [i - .45, i + .45], color="k", lw=6, ls=":")
    ax.set_xlim(0, horizon)
    ax.set_xticks(range(0, horizon + 1, max(1, horizon // 24)))
    ax.invert_yaxis()
    ax.set_title(title, fontsize=9)
    ax.grid(axis="x", alpha=.25)


def draw_inversion(ax, result, title, horizon):
    import matplotlib.pyplot as plt
    order = ["H", "M", "L"]
    cols = {"H": "#c0392b", "M": "#2e75b6", "L": "#70ad47"}
    t1 = [n for n, _ in result["timeline"]]
    segs = _segments(t1, order)
    for i, n in enumerate(order):
        ax.broken_barh(segs[n], (i - .35, .7),
                       facecolors=cols[n], edgecolor="white")
    blk = [(t, 1) for t, (n, b) in enumerate(result["timeline"]) if "H" in b]
    ax.broken_barh(blk, (-.35, .7), facecolors="#f5b7b1", hatch="xx",
                   edgecolor="#c0392b", linewidth=.3)
    ax.set_yticks(range(3), ["H (high)", "M (medium)", "L (low)"])
    ax.set_xlim(0, horizon)
    ax.set_xticks(range(horizon + 1))
    ax.invert_yaxis()
    ax.set_title(title, fontsize=9)
    ax.grid(axis="x", alpha=.25)
    ax.set_xlabel("time (ticks)")


if __name__ == "__main__":
    A = [Task("t1", 1, 4), Task("t2", 2, 6), Task("t3", 2, 12)]
    print(f"3-task set: U = {total_utilization(A):.3f}, "
          f"rm_bound(3) = {rm_bound(3):.3f}, "
          f"RM sufficient test passes: {total_utilization(A) <= rm_bound(3)}")
    B = A + [Task("t4", 1, 8)]
    print(f"4-task set: U = {total_utilization(B):.3f}, "
          f"rm_bound(4) = {rm_bound(4):.3f}, "
          f"RM sufficient test passes: {total_utilization(B) <= rm_bound(4)}, "
          f"EDF U <= 1: {total_utilization(B) <= 1}")
    o = priority_order(B)
    for i, k in enumerate(o):
        R, it, ok = rta(o, i)
        print(f"  RTA {k.name}: R = {R} (iterations {it}) <= D = {k.D}: {ok}")