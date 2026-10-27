# Real-Time Systems – Mini Project 2

Unit 2: Scheduling, Priority Inversion and Multiprocessor Partitioning.


## Contents

- **Mini Project 2.1** – `rts_sim.py` + `exp21.py`
  RM / DM / EDF / LLF simulator, RTA, priority inversion + PIP.
- **Mini Project 2.2** – `sched_tool.py` + `exp22.py`
  RM vs EDF schedulability comparison tool (list/CSV input).
- **Mini Project 2.3** – `partition.py` + `exp23.py`
  Partitioned multiprocessor scheduling (FF, FFD, BFD, WF).

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt