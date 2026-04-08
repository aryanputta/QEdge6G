# Experiment Log

## 2026-04-08

- Bootstrapped repo structure and core simulator.
- Added wireless, transport, edge, and optimization modules.
- Replaced the old exact baseline with a `scipy.optimize.milp` backend and kept branch-and-bound only as fallback.
- Added stronger flow-level TCP and QUIC dynamics, handoff penalty modeling, trace replay, tenant slicing, warm starts, and rolling-horizon forecasting.
- Expanded benchmark tooling with parameter sweeps and generated refreshed CSV artifacts for `wireless_dense`, `tcp_bursty`, `edge_overload`, `trace_replay`, `tenant_slicing`, and `sensitivity_sweep`.
- Reworked figures and notebooks into data-driven analysis artifacts.
- Added unit, integration, regression, and stress tests.

Notable smoke findings:

- MILP gives the strongest checked-in reference across dense, bursty, trace-backed, and slice-aware scenarios.
- Quantum-inspired search improves p95 latency over greedy in the checked-in `wireless_dense` run, but not consistently across every scenario.
- Safety fallback prevents the quantum-inspired solver from returning obviously worse allocations in overload-heavy cases.
