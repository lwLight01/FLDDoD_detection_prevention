"""fl_client/alert_sender.py"""

import httpx
import uuid
from typing import Dict, Any

class AlertSender:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    async def send_alert(self, client_id: uuid.UUID, src_ip: str, prob: float, shap_values: Dict[str, float]) -> bool:
        """Send DDoS alert to the Central Mitigation Engine."""
        payload = {
            "client_id": str(client_id),
            "src_ip": src_ip,
            "prediction_probability": prob,
            "shap_values": shap_values
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.api_url}/api/v1/alerts", json=payload, timeout=5.0)
                response.raise_for_status()
                return True
            except Exception as e:
                print(f"Failed to send alert: {e}")
                return False
