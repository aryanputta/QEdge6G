from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkloadClass:
    name: str
    latency_sla_ms: float
    base_demand_mbps: float
    compute_demand_units: int
    priority: float
    burstiness: float
    packet_size_bytes: int = 1500


@dataclass
class BaseStation:
    bs_id: str
    x: float
    y: float
    spectrum_mhz: int
    rb_budget: int


@dataclass
class EdgeServer:
    edge_id: str
    attached_agg: str
    x: float
    y: float
    capacity_units: int
    service_rate_units: int
    queue_buffer_units: int
    energy_cost: float = 1.0


@dataclass
class Link:
    link_id: str
    src: str
    dst: str
    capacity_mbps: int
    latency_ms: float
    buffer_mbits: int
    loss_rate: float = 0.0
    degraded_factor: float = 1.0


@dataclass
class PathState:
    path_id: str
    bs_id: str
    edge_id: str
    nodes: list[str]
    links: list[str]
    base_latency_ms: float
    capacity_mbps: int
    utilization: float
    queue_delay_ms: float
    loss_rate: float


@dataclass
class UserState:
    user_id: str
    attached_bs: str
    x: float
    y: float
    tenant_id: str
    slice_id: str
    workload: WorkloadClass
    demand_mbps: float
    predicted_demand_mbps: float
    channel_quality: float
    spectral_efficiency: float
    mobility_speed: float
    last_handoff_slot: int = -999
    handoff_count: int = 0
    handoff_penalty_ms: float = 0.0
    history_demand_mbps: list[float] = field(default_factory=list)
    history_channel_quality: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class ServiceTier:
    name: str
    throughput_factor: float
    utility_weight: float


@dataclass
class CandidateOption:
    option_id: str
    user_id: str
    bs_id: str
    edge_id: str
    path_id: str
    service_tier: str
    admitted: bool
    allocated_mbps: float
    compute_units: int
    radio_units: int
    path_units: int
    estimated_latency_ms: float
    estimated_loss_rate: float
    estimated_goodput_mbps: float
    objective_cost: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapacityConstraint:
    name: str
    capacity_units: int
    option_weights: dict[str, int]


@dataclass
class OptimizationInstance:
    scenario_name: str
    time_slot: int
    users: dict[str, UserState]
    options_by_user: dict[str, list[CandidateOption]]
    capacities: dict[str, CapacityConstraint]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocationDecision:
    user_id: str
    option_id: str
    edge_id: str | None
    path_id: str | None
    service_tier: str
    admitted: bool
    allocated_mbps: float
    goodput_mbps: float
    packet_loss_rate: float
    latency_ms: float
    queue_delay_ms: float
    compute_delay_ms: float
    objective_cost: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SolverResult:
    solver_name: str
    decisions: list[AllocationDecision]
    objective_value: float
    runtime_s: float
    violations: list[str] = field(default_factory=list)
    energy: float | None = None
    quality_gap: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepMetrics:
    scenario_name: str
    time_slot: int
    solver_name: str
    mean_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_mbps: float
    goodput_mbps: float
    packet_loss_rate: float
    fairness_index: float
    queue_delay_ms: float
    edge_utilization: float
    transport_utilization: float
    wireless_utilization: float
    solver_runtime_s: float
    objective_value: float
    quality_gap: float | None
    constraint_violation_count: int
    dominant_bottleneck: str
    admission_rate: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSummary:
    scenario_name: str
    solver_name: str
    metrics: dict[str, float | str | None]
