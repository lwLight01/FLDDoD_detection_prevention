import time
from ryu.lib import hub

class FlowExtractor:
    """
    Simulates real-time flow extraction.
    In a true production environment, we'd use Ryu's EventOFPFlowStatsReply.
    For this simulation, this module calculates flow duration and pushes CSV rows 
    to the Federated Edge Client.
    """
    def __init__(self, ryu_app):
        self.ryu_app = ryu_app
        self.flow_cache = {}
        self.monitor_thread = hub.spawn(self._monitor)

    def _monitor(self):
        while True:
            for dp in self.ryu_app.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10) # 10 second window

    def _request_stats(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # Request flow stats from all tables
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    def process_stats(self, ev):
        """Called by the main Ryu app when stats arrive."""
        msg = ev.msg
        for stat in msg.body:
            # Calculate simple features: duration, packet_count, byte_count
            if 'ipv4_src' in stat.match:
                src = stat.match['ipv4_src']
                duration = stat.duration_sec
                pkts = stat.packet_count
                bytes_ = stat.byte_count
                
                # We would normally write this to a CSV or push directly to the FL client.
                # In Milestone 40, we format the data so the FT-Transformer can ingest it.
                self.flow_cache[src] = {
                    "Flow Duration": duration,
                    "Total Fwd Packets": pkts,
                    "Total Length of Fwd Packets": bytes_
                }
                # Log extraction for simulation visibility
                self.ryu_app.logger.debug(f"[Flow Extractor] Extracted stats for {src}: {self.flow_cache[src]}")
