from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TraceRecord:
    time_slot: int
    user_id: str
    demand_mbps: float
    channel_quality: float
    attached_bs: str
    workload: str
    tenant_id: str
    slice_id: str
    mobility_speed_mps: float


class TraceReplayDataset:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self.records_by_time: dict[int, list[TraceRecord]] = defaultdict(list)
        self.records_by_user: dict[str, list[TraceRecord]] = defaultdict(list)
        with Path(path).open("r", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                record = TraceRecord(
                    time_slot=int(row["time_slot"]),
                    user_id=row["user_id"],
                    demand_mbps=float(row["demand_mbps"]),
                    channel_quality=float(row.get("channel_quality", 0.7)),
                    attached_bs=row.get("attached_bs", "bs0"),
                    workload=row.get("workload", "video"),
                    tenant_id=row.get("tenant_id", "tenant0"),
                    slice_id=row.get("slice_id", "eMBB"),
                    mobility_speed_mps=float(row.get("mobility_speed_mps", 0.5)),
                )
                self.records_by_time[record.time_slot].append(record)
                self.records_by_user[record.user_id].append(record)

        for user_records in self.records_by_user.values():
            user_records.sort(key=lambda record: record.time_slot)

    def initial_records(self) -> list[TraceRecord]:
        if not self.records_by_time:
            return []
        return list(self.records_by_time[min(self.records_by_time)])

    def slot_records(self, time_slot: int) -> dict[str, TraceRecord]:
        if time_slot in self.records_by_time:
            return {record.user_id: record for record in self.records_by_time[time_slot]}
        latest_time = max((slot for slot in self.records_by_time if slot <= time_slot), default=None)
        if latest_time is None:
            return {}
        return {record.user_id: record for record in self.records_by_time[latest_time]}
