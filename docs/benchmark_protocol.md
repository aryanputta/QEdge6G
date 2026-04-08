# Benchmark Protocol

Benchmark rules for QEdge6G:

1. Use the same scenario seed for every solver.
2. Rebuild topology and user state fresh for each solver run.
3. Use the MILP exact solver whenever the user count is under the configured cutoff.
4. Report both optimization-side objective values and execution-side systems metrics.
5. Keep smoke benchmarks small and mark them clearly as smoke results.

Required scenario families in this repo:

- dense wireless contention
- bursty TCP traffic
- edge overload
- mobility or link degradation
- backhaul bottlenecks
- mixed workload classes
- trace replay
- tenant slicing
- parameter sweeps over forecast error and capacity

Required reported metrics:

- mean latency
- p95 latency
- p99 latency
- throughput
- goodput
- packet loss
- fairness
- queue delay
- edge utilization
- solver runtime
- solution quality gap
- constraint violation count

Interpretation rule:

- objective quality and system latency are related but not identical
- a solver can improve p95 latency while still losing on the composite objective
- a solver can also be rejected by a safety fallback if it degrades latency too much relative to the warm-start baseline
- that disagreement should be documented, not averaged away
