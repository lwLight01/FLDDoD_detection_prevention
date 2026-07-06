from ryu.app.wsgi import ControllerBase, route
from ryu.ofproto import ofproto_v1_3
import json
from webob import Response

class MitigationController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(MitigationController, self).__init__(req, link, data, **config)
        self.ryu_app = data['ryu_app']

    @route('mitigation', '/api/v1/mitigate', methods=['POST'])
    def apply_mitigation(self, req, **kwargs):
        try:
            body = json.loads(req.body)
            src_ip = body.get('src_ip')
            action = body.get('action') # e.g., 'drop' or 'rate_limit'
            
            if not src_ip or not action:
                return Response(status=400, body=json.dumps({"error": "Missing src_ip or action"}))

            # Apply to all active datapaths
            for dp in self.ryu_app.datapaths.values():
                ofproto = dp.ofproto
                parser = dp.ofproto_parser
                
                # Match packets from the malicious source IP
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip)
                
                if action == 'drop':
                    # Drop packets (empty instruction set)
                    inst = []
                    # High priority to override normal forwarding
                    mod = parser.OFPFlowMod(datapath=dp, priority=100, match=match, instructions=inst)
                    dp.send_msg(mod)
                    
            return Response(status=202, body=json.dumps({"status": "Mitigation applied"}))
        except Exception as e:
            return Response(status=500, body=json.dumps({"error": str(e)}))

    @route('mitigation', '/api/v1/mitigate', methods=['DELETE'])
    def remove_mitigation(self, req, **kwargs):
        try:
            body = json.loads(req.body)
            src_ip = body.get('src_ip')
            
            if not src_ip:
                return Response(status=400, body=json.dumps({"error": "Missing src_ip"}))

            for dp in self.ryu_app.datapaths.values():
                ofproto = dp.ofproto
                parser = dp.ofproto_parser
                
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip)
                
                # OFPFC_DELETE removes matching flows
                mod = parser.OFPFlowMod(
                    datapath=dp,
                    command=ofproto.OFPFC_DELETE,
                    out_port=ofproto.OFPP_ANY,
                    out_group=ofproto.OFPG_ANY,
                    priority=100,
                    match=match
                )
                dp.send_msg(mod)
                    
            return Response(status=200, body=json.dumps({"status": "Mitigation revoked"}))
        except Exception as e:
            return Response(status=500, body=json.dumps({"error": str(e)}))
