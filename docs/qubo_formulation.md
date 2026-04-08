# QUBO Formulation

## Variable Mapping

For each user `u`, candidate edge `e`, path `p`, and service tier `t`, QEdge6G creates one binary option variable:

`x_{u,e,p,t} = 1` if the allocation is selected, else `0`

Each user also receives a `drop` option so the solver can represent overload or SLA protection explicitly.

## Objective

Each admitted option contributes a diagonal cost made from:

- estimated end-to-end latency
- SLA miss penalty
- loss penalty
- compute placement pressure
- fairness reward

The drop option carries an explicit penalty so dropping is allowed but never free.

## Constraints

QEdge6G encodes:

- one-hot user assignment
- radio budget per base station
- bandwidth budget per path
- compute budget per edge
- tenant-slice radio caps
- tenant-slice edge caps

Capacity constraints use slack variables in binary decomposition form:

`sum(w_i x_i) + sum(s_k 2^k) = C`

This keeps the constraint quadratic while allowing exact validation after decoding.

## Why QUBO Fits

- the decision space is discrete
- the resource constraints are combinatorial
- exact MILP search scales poorly as candidate sets and slice-aware constraints expand
- solver comparisons become cleaner when every method sees the same option set

## What Is Lost

- continuous bandwidth becomes tiered bandwidth
- queueing is estimated during optimization and realized after execution
- the QUBO size grows with both candidate options and slack variables

## Practical Bottleneck

The QUBO becomes expensive when:

- user count rises
- candidate path count rises
- bandwidth units get too fine
- capacity values require many slack bits

That scaling pain is a feature of the analysis, not something this repo tries to hide.
