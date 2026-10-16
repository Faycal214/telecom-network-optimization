# Experimental design

## Research question

How much do MIR-based cutset inequalities change the computational behavior of a capacitated network-design MILP, and how does a simple single-path greedy heuristic compare with an exact optimization baseline?

## Methods

1. **Base MILP:** Pyomo formulation solved by HiGHS.
2. **MILP + MIR cutset inequalities:** same model with all nontrivial undirected MIR cutset inequalities enumerated before solving.
3. **Greedy heuristic:** route demands in descending volume order; for each demand, evaluate candidate simple paths using routing cost plus incremental module-provisioning cost; then select modules to cover aggregate link loads.

## Instance and scenarios

The starter instance is the five-node, eight-link, three-demand example published with the SNDlib native-format documentation. Demand scaling by factors 1, 2, and 3 is used as a transparent stress test. Scaled scenarios are derived experiments, not additional official SNDlib benchmarks.

## Metrics

- Feasibility: all demand balances and link-capacity constraints must hold.
- Objective value: routing cost + installed-module cost.
- Runtime in seconds.
- Solver best lower/upper bounds and relative MIP gap when available.
- Heuristic relative gap to a proven optimum, only when an exact solver proves optimality.
- Number of MIR cutset inequalities added.

For minimization, the solver gap is (UB−LB)/|LB|×100% where the bounds are available and |LB|>0. The heuristic gap is (heuristic objective−proven optimum)/|proven optimum|×100%, reported only when the optimum is proven and the denominator is nonzero.

## Reproducibility

The instance, demand scale, capacity mode, solver, time limit, method, runtime, solver bounds, and number of cuts are stored in CSV. Greedy routes and edge loads are written to JSON. Experiments should be run several times for meaningful runtime comparison on larger instances; this tiny starter instance is primarily a correctness demonstration.

## Interpretation caution

Static exhaustive cut addition is not identical to the paper's callback-based dynamic separation. On tiny instances, overhead may dominate and adding cuts may not reduce runtime. We report results as observed and do not assume that cut strengthening must make every instance faster.
