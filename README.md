# Telecom Network Optimization

Research-oriented implementation and experimental study of mathematical optimization methods for telecommunication network design.

This project investigates how mathematical optimization and heuristic algorithms can be used to design efficient and reliable telecommunication networks.

The project uses publicly available **SNDlib (Survivable Network Design Library)** benchmark instances and focuses on reproducing a research formulation, implementing it independently, and developing and evaluating additional optimization algorithms.

## Objectives

The main objectives are:

* Understand and reproduce a published mathematical optimization model for telecom network design.
* Formulate the problem independently using **Pyomo**.
* Solve benchmark instances using exact optimization solvers.
* Develop custom heuristic and/or metaheuristic algorithms.
* Compare exact and heuristic approaches in terms of solution quality, runtime, feasibility, and optimality gap.
* Investigate the scalability of the proposed approaches on increasingly difficult network instances.

## Research Workflow

```text
Research Paper
      ↓
Mathematical Formulation
      ↓
Pyomo Implementation
      ↓
SNDlib Benchmark Instances
      ↓
Exact Optimization
      ↓
Custom Heuristics
      ↓
Experimental Evaluation
      ↓
Analysis & Conclusions
```

## Problem

The project studies a telecommunication network design problem in which a network is represented as a graph:

$$
G=(V,E)
$$

where \(V\) represents network nodes and \(E\) represents communication links.

The optimization model determines how network resources should be designed or allocated while satisfying the required connectivity, capacity, demand, and survivability constraints.

The exact formulation used in the project will be documented in [`docs/mathematical_model.md`](docs/mathematical_model.md) after the selected research paper has been studied and reproduced.

## Benchmark

The experiments use instances from the **Survivable Network Design Library (SNDlib)**.

SNDlib provides publicly available reference network topologies and traffic-demand data for telecommunication network optimization.

The benchmark information and download instructions are documented in [`data/README.md`](data/README.md).

## Methods

The project will progressively implement:

### Exact optimization

* Mixed-Integer Linear Programming (MILP)
* Pyomo mathematical models
* Exact optimization solvers such as HiGHS, CBC, Gurobi, or CPLEX when available

### Heuristic optimization

Depending on the structure of the selected problem, possible approaches include:

* Greedy algorithms
* Local Search
* Simulated Annealing
* Tabu Search
* Genetic Algorithms
* Problem-specific heuristics

The final algorithms will be selected after analyzing the mathematical structure of the problem.

## Evaluation

Algorithms will be evaluated using:

* Objective value
* Feasibility
* Runtime
* Optimality gap
* Best-known solution
* Solver lower/upper bounds when available
* Scalability with respect to network size

For a minimization problem, the optimality gap can be measured as:

$$
Gap(\%) =
\frac{f_{\mathrm{sol}}-f_{\mathrm{best}}}
{|f_{\mathrm{best}}|}
\times 100
$$

where \(f_{\mathrm{sol}}\) is the objective value obtained by an algorithm and \(f_{\mathrm{best}}\) is the reference best-known or proven optimal objective value.

## Reproducibility

The project aims to keep experiments reproducible.

Each experiment will specify:

* Benchmark instance
* Mathematical formulation
* Solver
* Solver parameters
* Time limit
* Algorithm parameters
* Random seed when applicable
* Hardware/software environment

Experiment configurations will be stored in [`experiments/configs/`](experiments/configs/), while generated results will be stored in [`experiments/results/`](experiments/results/).

## Project Status

🚧 **In progress**

Current stage:

* [x] Define research direction
* [x] Select SNDlib as benchmark family
* [ ] Study the selected research paper
* [ ] Formalize the mathematical model
* [ ] Implement the baseline MILP in Pyomo
* [ ] Validate the formulation
* [ ] Implement custom optimization algorithms
* [ ] Run benchmark experiments
* [ ] Analyze results
* [ ] Write the final technical report

## Technologies

* Python
* Pyomo
* NetworkX
* NumPy
* Pandas
* Matplotlib
* Jupyter
* MILP solvers

## Research References

The principal research paper and additional related literature will be documented in [`papers/README.md`](papers/README.md).

## Author

**Faycal Alikacem**

MSc student in Stochastic Modeling and Forecasting
Operations Research · Mathematical Optimization · Machine Learning

GitHub: [Faycal214](https://github.com/Faycal214)

---

> **Research principle:** reproduce first, understand second, improve third.
