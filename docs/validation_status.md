# Validation status (initial prototype)

## Checks completed

- Parsed the included SNDlib native-format example: 5 nodes, 8 links, and 3 point-to-point demands.
- Verified the integer MIR coefficient function against hand-checkable values.
- Generated MIR cutset rows for the small instance.
- Ran the greedy routing heuristic and checked that every demand has a route and all link loads are covered by preinstalled capacity plus selected modules.
- Automated tests: 4 passed.

For the base example, the greedy heuristic reports total objective 5,330, consisting of routing cost 2,030 and module cost 3,300. This is a heuristic value only; it should not be called optimal unless the exact solver independently proves the same objective.

## Solver execution still required

The current execution environment did not have Pyomo or highspy installed and package-network access was unavailable. Therefore the checked-in Pyomo model has been syntax-checked but has **not yet been run through the Pyomo + HiGHS backend in this environment**.

Before presenting solver performance results, run:

    python -m pip install -e ".[dev]"
    pytest
    python scripts/run_experiment.py --instance data/examples/network.txt --scales 1 2 3 --time-limit 60

Inspect the generated CSV. Confirm both MILP variants terminate successfully and, ideally, prove optimality. Only then use their bounds/objectives to report the heuristic gap and discuss whether cutset inequalities improved runtime.

## Interpretation warning

The 5-node official documentation example is a correctness demonstration, not enough evidence for a general performance claim. The next study should use several larger original SNDlib instances with carefully documented model settings.
