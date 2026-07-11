"""sdn_controller/flow_extractor.py

Milestone 40 — Real-time flow feature extraction from Ryu OpenFlow stats.

Polls per-switch flow statistics every 10 seconds, calculates tabular features
that match the FT-Transformer's input schema, and exposes them via
``get_latest_flows()`` for consumption by the edge inference agent.
"""

from __future__ import annotations

import csv
import io
import time
from typing import Dict, List, Optional

from ryu.lib import hub


# Features that the FT-Transformer expects (must match dataset.py constants)
FEATURE_COLUMNS: List[str] = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Init_Win_bytes_forward",
    "Active Mean",
    "Idle Mean",
    "Protocol",
    "TCP Flags",
    "Label",
]


class FlowExtractor:
    """Monitors Ryu datapaths and extracts tabular flow features.

    Periodically requests ``OFPFlowStatsRequest`` from each connected switch
    and converts the reply into feature rows compatible with the FT-Transformer
    input schema defined in ``src/fl_client/dataset.py``.
    """

    def __init__(self, ryu_app, poll_interval: int = 10) -> None:
        """
        Parameters
        ----------
        ryu_app:
            Reference to the parent ``BaseSwitch`` Ryu application.
        poll_interval:
            Seconds between stats polling cycles.
        """
        self.ryu_app = ryu_app
        self.poll_interval = poll_interval

        # flow_cache: src_ip → feature dict
        self._flow_cache: Dict[str, Dict] = {}

        # Track when each flow was first seen to compute duration
        self._flow_start: Dict[str, float] = {}

        # Snapshot buffer flushed after each poll cycle
        self._completed_flows: List[Dict] = []

        # Start background monitor thread
        self._monitor_thread = hub.spawn(self._monitor)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_latest_flows(self, clear: bool = True) -> List[Dict]:
        """Return and optionally clear the completed-flow snapshot buffer.

        Called by the inference agent to retrieve newly captured flows.
        """
        flows = list(self._completed_flows)
        if clear:
            self._completed_flows.clear()
        return flows

    def to_csv_string(self, flows: Optional[List[Dict]] = None) -> str:
        """Serialize flow records to a CSV string for debugging / logging."""
        rows = flows if flows is not None else self._completed_flows
        if not rows:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=FEATURE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    # ------------------------------------------------------------------
    # Ryu event handlers
    # ------------------------------------------------------------------

    def process_stats(self, ev) -> None:
        """Called by ``BaseSwitch`` when an ``OFPFlowStatsReply`` arrives."""
        msg = ev.msg
        now = time.time()

        for stat in msg.body:
            # Only process flows with an IPv4 source address in the match
            if "ipv4_src" not in stat.match:
                continue

            src_ip: str = stat.match["ipv4_src"]
            dst_ip: str = stat.match.get("ipv4_dst", "0.0.0.0")
            protocol: int = stat.match.get("ip_proto", 0)

            # Duration: prefer stat.duration_sec; fall back to wall-clock delta
            if stat.duration_sec > 0:
                duration = float(stat.duration_sec) + float(stat.duration_nsec) * 1e-9
            else:
                start = self._flow_start.setdefault(src_ip, now)
                duration = max(now - start, 1e-6)

            pkts: int = stat.packet_count
            bytes_: int = stat.byte_count

            # Bytes/s and Packets/s
            flow_bytes_s = bytes_ / duration if duration > 0 else 0.0
            flow_pkts_s = pkts / duration if duration > 0 else 0.0

            # TCP flags from match (if present)
            tcp_flags: int = stat.match.get("tcp_flags", 0) if protocol == 6 else 0

            # Packet length statistics (approximate from aggregate bytes)
            pkt_len_mean = (bytes_ / pkts) if pkts > 0 else 0.0
            # Without per-packet data we approximate min/max around the mean
            pkt_len_max = pkt_len_mean * 1.2
            pkt_len_min = max(pkt_len_mean * 0.8, 0.0)

            feature_row: Dict = {
                "Flow Duration": round(duration, 6),
                "Total Fwd Packets": pkts,
                "Total Bwd Packets": 0,              # Single-direction stat
                "Fwd Packet Length Max": round(pkt_len_max, 2),
                "Fwd Packet Length Min": round(pkt_len_min, 2),
                "Fwd Packet Length Mean": round(pkt_len_mean, 2),
                "Flow Bytes/s": round(flow_bytes_s, 4),
                "Flow Packets/s": round(flow_pkts_s, 4),
                "Init_Win_bytes_forward": stat.match.get("tcp_src", 0),
                "Active Mean": 0.0,                  # Not available from OFP stats
                "Idle Mean": 0.0,
                "Protocol": protocol,
                "TCP Flags": tcp_flags,
                "Label": 0,                          # Unknown — inference will classify
                "_src_ip": src_ip,
                "_dst_ip": dst_ip,
            }

            self._flow_cache[src_ip] = feature_row
            self._completed_flows.append(feature_row)

            self.ryu_app.logger.debug(
                "[FlowExtractor] src=%s duration=%.3fs pkts=%d bytes=%d",
                src_ip,
                duration,
                pkts,
                bytes_,
            )

    # ------------------------------------------------------------------
    # Background monitor
    # ------------------------------------------------------------------

    def _monitor(self) -> None:
        """Periodically request flow statistics from all connected datapaths."""
        while True:
            for dp in self.ryu_app.datapaths.values():
                self._request_stats(dp)
            hub.sleep(self.poll_interval)

    def _request_stats(self, datapath) -> None:
        """Send an OFPFlowStatsRequest to a single datapath."""
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
