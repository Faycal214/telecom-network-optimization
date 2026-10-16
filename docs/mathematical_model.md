# Mathematical model

## Scope

The first implementation is an **undirected capacitated multicommodity network-design MILP**. Physical links have shared capacity across both traffic directions. Routing variables are continuous, and module variables are integer in modular mode. Fixed-charge costs, hop limits, admissible-path restrictions, and survivability requirements are excluded.

This is a deliberate restricted implementation inspired by Raack et al. (the paper), not a complete implementation of all directed, bidirected, and undirected variants in that paper.

## Sets and data

- V: network nodes.
- E: physical undirected links.
- D: origin-destination traffic demands.
- M(e): installable module types available on link e.
- q_d: volume of demand d, with source s_d and target t_d.
- b_e: preinstalled capacity on link e.
- c_em: capacity of module m available on link e.
- k_em: installation cost of module m on link e.
- r_e: routing cost per flow unit over link e.

Every physical link e={i,j} is represented by two directed arcs (i,j) and (j,i) for flow accounting.

## Decision variables

- f_dij ≥ 0: flow of demand d along directed arc (i,j).
- x_em ∈ Z₊: number of modules of type m installed on physical link e. In explicit mode, x_em is binary and at most one module may be selected per link.

## Objective

Minimize routing cost plus capacity-installation cost:

min Σ_e r_e Σ_d (f_d,uv + f_d,vu) + Σ_e Σ_m k_em x_em.

The cost of preinstalled capacity is treated as sunk and omitted because it does not depend on the decisions. Fixed-charge costs are excluded to match the paper's stated computational configuration.

## Flow conservation

For every demand d and node v:

outflow(d,v) − inflow(d,v) = q_d if v=s_d; −q_d if v=t_d; otherwise 0.

## Shared undirected link capacity

For every physical link e={u,v}:

Σ_d (f_duv + f_dvu) ≤ b_e + Σ_m c_em x_em.

## MIR cutset strengthening

For a nontrivial node subset S, let E(S) be links crossing between S and V\S. Let Q(S) be the total OD traffic whose source and destination lie on opposite sides of the cut. The capacity already installed across the cut is B(S)=Σ_{e∈E(S)} b_e. The residual capacity requirement is d(S)=max(0,Q(S)−B(S)).

For each reference module capacity c_t and positive residual requirement d(S), add the MIR cutset inequality:

Σ_{e∈E(S)} Σ_{m∈M(e)} F_{d(S),c_t}(c_em) x_em ≥ F_{d(S),c_t}(d(S)),

where F is the integer MIR function from Eq. (5) of Raack et al. The implementation enumerates all nontrivial undirected cuts, so it is intended for small instances. This is a static exhaustive cutset experiment, not the paper's dynamic Algorithms A/B/C separation procedure.

## Model limitations

- The model covers the undirected shared-capacity case only.
- The exhaustive cut generator is exponential in |V| and intentionally limited to small networks.
- The sample network is the official SNDlib native-format documentation example, not one of the 54 experimental configurations from the paper.
- Before claiming a full paper reproduction, the formulation and objectives must be validated against the paper's selected SNDlib configuration and reference results.
