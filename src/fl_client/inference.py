"""fl_client/inference.py"""

import asyncio
import uuid
from typing import Dict
from fl_client.alert_sender import AlertSender

class InferenceAgent:
    def __init__(self, client_id: uuid.UUID, alert_sender: AlertSender):
        self.client_id = client_id
        self.alert_sender = alert_sender
        self.threshold = 0.85
        
    async def process_flow(self, src_ip: str, flow_features: dict):
        """
        Mock processing of a network flow.
        In a real scenario, this would run PyTorch inference and SHAP explainability.
        """
        # Mock PyTorch model inference
        prob = self._mock_inference(flow_features)
        
        if prob > self.threshold:
            # Mock SHAP explanation
            shap_values = self._mock_shap(flow_features)
            await self.alert_sender.send_alert(self.client_id, src_ip, prob, shap_values)
            
    def _mock_inference(self, features: dict) -> float:
        # Dummy logic: if "total_fwd_packets" > 1000, consider it an attack
        if features.get("total_fwd_packets", 0) > 1000:
            return 0.95
        return 0.1
        
    def _mock_shap(self, features: dict) -> Dict[str, float]:
        return {
            "total_fwd_packets": 0.8,
            "flow_duration": 0.1,
            "protocol_TCP": 0.05
        }

async def main():
    client_id = uuid.uuid4()
    sender = AlertSender()
    agent = InferenceAgent(client_id, sender)
    
    # Simulate receiving an anomalous flow
    print("Simulating anomalous flow...")
    await agent.process_flow("192.168.1.100", {"total_fwd_packets": 5000})
    print("Flow processed.")

if __name__ == "__main__":
    asyncio.run(main())
