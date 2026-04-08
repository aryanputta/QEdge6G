# System Assumptions

Synthetic does not mean arbitrary. The simulator assumes:

- base stations have finite spectrum and radio block budgets
- users experience time-varying channel quality, optional mobility, and handoff penalties
- backhaul links have fixed capacities, finite buffers, and queueing delay
- edge servers have finite service rates and can overload
- tenant slices can cap radio and edge share
- each decision step represents a short scheduling window rather than a full second of serialized service

What the synthetic model approximates:

- dense urban cells with shared backhaul congestion
- bursty XR, video, inference, and telemetry workloads
- edge clusters where the nearest edge is not always the best edge
- replayed demand traces with tenant and slice labels

Known simplifications:

- no packet-level MAC or PHY simulation
- no packet-level transport emulator
- no full RAN control-plane handover protocol simulation
- the bundled trace replay is illustrative and not yet drawn from a public carrier dataset

These simplifications are intentional so the repo can benchmark optimization tradeoffs cleanly without hiding behind a massive simulation stack.
