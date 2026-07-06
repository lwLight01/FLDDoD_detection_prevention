"""mitigation_engine/services/sdn_client.py"""

import httpx
from mitigation_engine.config import settings

class SDNClient:
    def __init__(self):
        self.base_url = settings.ryu_rest_api_url
        
    async def push_rule(self, rule_payload: dict) -> bool:
        """Push JSON OpenFlow rule to Ryu Controller."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/stats/flowentry/add",
                    json=rule_payload,
                    timeout=5.0
                )
                response.raise_for_status()
                return True
            except Exception as e:
                # Log error in real app
                return False

    async def delete_rule(self, rule_payload: dict) -> bool:
        """Delete JSON OpenFlow rule from Ryu Controller."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/stats/flowentry/delete",
                    json=rule_payload,
                    timeout=5.0
                )
                response.raise_for_status()
                return True
            except Exception as e:
                return False
