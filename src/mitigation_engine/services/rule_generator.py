"""mitigation_engine/services/rule_generator.py"""

from typing import Dict, Any
from shared.enums import MitigationLevel, SeverityLevel

class XAIRuleGenerator:
    @staticmethod
    def generate_sdn_rule(src_ip: str, shap_values: Dict[str, float], severity: SeverityLevel) -> tuple[MitigationLevel, dict]:
        """
        Translate SHAP features and severity to SDN OpenFlow rules.
        """
        if severity == SeverityLevel.LOW:
            return MitigationLevel.NONE, {}
            
        action_type = MitigationLevel.NONE
        payload = {"src_ip": src_ip}
        
        if severity == SeverityLevel.MEDIUM:
            action_type = MitigationLevel.RATE_LIMIT
            payload["rate"] = 100 # limit to 100 pps
        elif severity == SeverityLevel.HIGH:
            action_type = MitigationLevel.ISOLATE
            payload["vlan"] = "quarantine"
        else: # CRITICAL
            action_type = MitigationLevel.QUARANTINE
            payload["action"] = "drop"
            
        # Refine based on SHAP
        top_feature = max(shap_values, key=shap_values.get) if shap_values else None
        if top_feature:
            if "TCP" in top_feature.upper() or "SYN" in top_feature.upper():
                payload["protocol"] = "TCP"
                if action_type == MitigationLevel.RATE_LIMIT:
                    payload["rate"] = 50
            elif "UDP" in top_feature.upper():
                payload["protocol"] = "UDP"
                
        return action_type, payload
