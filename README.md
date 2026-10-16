# Telecom Network Optimization

**A research-oriented Operations Research prototype for capacitated telecommunication network design.**

This project implements an undirected capacitated multicommodity network-design MILP, adds MIR-based cutset inequalities derived from a research paper, and compares the MILP solutions with a path-based greedy heuristic.

> **Scope note:** the current version is a reproducible starter study on the official SNDlib native-format documentation example. It does **not** claim to reproduce all 54 experimental configurations or the callback-based Algorithms A/B/C from the paper.

## Research question

How do MIR-based cutset inequalities affect an exact network-design formulation, and how close can a simple greedy heuristic get to a proven optimum on small telecom network instances?

## Research paper

Raack, C., Koster, A. M. C. A., Orlowski, S., & Wessely, R. *Capacitated Network Design Using General Flow-Cutset Inequalities.*

- [Download the paper](https://optimization-online.org/wp-content/uploads/2006/11/1525.pdf)
- [SNDlib-MIPs alternative dataset paper/data record](https://doi.org/10.5281/zenodo.8021237) (not the primary input used here; its formulations differ from those in the paper)

## What is implemented?

| Method | Description |
|---|---|
| Base MILP | Pyomo model solved with the open-source HiGHS MIP solver |
| MILP + MIR cuts | Same model with static MIR cutset inequalities enumerated for every nontrivial undirected cut |
| Greedy heuristic | Routes demands in descending-volume order using candidate simple paths scored by routing and incremental capacity-installation cost |

## Model scope

The current model includes:

- Undirected physical links with shared capacity in both traffic directions
- Continuous multicommodity flow variables
- Integer capacity-module variables (Modular model)
- Preinstalled capacity
- Per-unit routing costs and module-installation costs
- MIR cutset inequalities for small instances

The current model excludes fixed-charge costs, survivability constraints, node capacities, hop limits, and explicit admissible-path restrictions. See [`docs/mathematical_model.md`](docs/mathematical_model.md) for the equations and assumptions.

## Data

The starter instance [`data/examples/network.txt`](data/examples/network.txt) is taken from the [official SNDlib native-format example](https://sndlib.put.poznan.pl/html/docu/io-formats/native/examples/network.txt).

The original SNDlib network archive provides topologies, link attributes, and demand matrices in native ASCII and XML formats: [SNDlib networks](https://sndlib.put.poznan.pl/networks.overview.action). The parser here targets the native ASCII fields required by the model.

The separate [SNDlib-MIPs collection](https://zenodo.org/records/8021237) has 289 pre-formulated MILPs derived from SNDlib, but modifies several formulation choices. It is not treated as a drop-in equivalent of the original benchmark models.

## Installation

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

This installs Pyomo, the HiGHS Python interface, NetworkX, and development tools. No commercial solver licence is needed.

## Run the experiment

```bash
python scripts/run_experiment.py \
  --instance data/examples/network.txt \
  --scales 1 2 3 \
  --capacity-mode modular \
  --time-limit 60
```

The runner compares the base MILP, the MILP with MIR cutset inequalities, and the greedy heuristic. It writes:

- `experiments/results/summary.csv` — objective values, runtime, solver bounds/gap, feasibility and cuts added
- `experiments/results/heuristic_routes.json` — routes, edge loads and module choices from the heuristic

Run tests with:

```bash
pytest
```

## Evaluation methodology

The comparison records:

- Feasibility
- Objective value (routing cost + module cost)
- Runtime
- Solver lower/upper bounds and MIP gap when available
- Heuristic relative gap to a **proven optimum**, only when the solver establishes optimality
- Number of cutset inequalities added

For minimization, when valid bounds are available, the solver gap is `(UB - LB) / abs(LB) × 100%`. The heuristic gap is calculated against the proven optimal objective, never against an unproven incumbent.

The starter network is deliberately small and useful primarily for checking correctness. Runtime conclusions should not be generalized from this example; the next research stage is to run a selected set of larger original SNDlib networks and compare multiple runs with fixed solver settings.

## Validation status

See [docs/validation_status.md](docs/validation_status.md) for checks completed, the heuristic example value, and the solver run that remains to be executed in an environment with Pyomo and HiGHS installed.

## Limitations and next steps

1. Validate the Pyomo model and objective against the paper's exact model specification for a selected SNDlib configuration.
2. Test on selected original SNDlib networks rather than only the documentation example.
3. Compare modular and explicit capacity variants.
4. Evaluate whether static cutset inequalities improve performance; exhaustive enumeration is exponential and is only enabled for networks with at most 18 nodes.
5. Extend toward a dynamic separation routine inspired by the paper's Algorithms B/C.
6. Improve the heuristic with local search and multi-start routing.

## Author

**Faycal Alikacem** — MSc student in Stochastic Modeling and Forecasting / Operations Research.

## Citation and data attribution

Please cite the primary paper and the SNDlib dataset papers when reporting results. The SNDlib starter file is attributed in `data/README.md` and `papers/README.md`.

---

**Research principle:** formulate carefully, establish a baseline, evaluate honestly, then improve.

## Publish to GitHub

After reviewing the files and running the tests, publish this folder to the existing repository with:

    bash scripts/publish_to_github.sh

The script clones Faycal214/telecom-network-optimization, copies the project files into it, creates a commit, and pushes to the default branch. GitHub write authentication must already work on your machine. Review the staged changes before running if the repository contains work you want to preserve.
