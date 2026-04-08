# Failure Analysis

QEdge6G is designed to expose failure, not just success.

## Observed in Checked-In Smoke Runs

- `wireless_dense`: the quantum-inspired solver improved p95 latency over greedy, but still trailed the MILP reference on objective quality.
- `tcp_bursty`: the quantum-inspired solver did not beat greedy on p95 latency and still paid a large quality gap versus MILP.
- `edge_overload`: the quantum-inspired solver fell back to the greedy allocation because the search result violated the safety gate.
- `trace_replay`: the MILP backend gave the cleanest latency profile on the bundled trace-backed scenario.
- `shortest_path_nearest_edge`: consistently hurt tail latency when transport hotspots formed.

## Why the Optimizer Can Fail

- QUBO discretization can favor a path or tier that is slightly too coarse.
- The objective mixes latency, fairness, and admission pressure, so lower objective does not always mean best p95.
- Predictive error can steer capacity toward the wrong users when future demand shifts.
- MILP can become the runtime bottleneck well before the simulated system does.

## Current Honest Limits

- The exact baseline is far stronger now, but it is still best used as a moderate-scale reference rather than the online default.
- The quantum-inspired solver is slower than heuristics by orders of magnitude at smoke scale.
- Transport realism is improved, but a packet-level simulator could still change the ranking in edge cases.

## What to Investigate Next

- finer-grained bandwidth discretization
- rolling-horizon warm starts
- stronger congestion forecasting
- real trace replay for validation
- better quantum-inspired moves that reduce dependence on the safety fallback
