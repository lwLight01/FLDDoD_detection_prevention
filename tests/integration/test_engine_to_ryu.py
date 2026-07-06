"""tests/integration/test_engine_to_ryu.py"""

import pytest
from mitigation_engine.services.sdn_client import SDNClient
from mitigation_engine.services.rule_generator import XAIRuleGenerator
from shared.enums import SeverityLevel, MitigationLevel

@pytest.mark.asyncio
async def test_xai_rule_generator():
    """Test translating SHAP features to OpenFlow payload."""
    shap_values = {"TCP_SYN": 0.9, "UDP_length": 0.05}
    severity = SeverityLevel.CRITICAL
    
    action, payload = XAIRuleGenerator.generate_sdn_rule("192.168.1.50", shap_values, severity)
    
    assert action == MitigationLevel.QUARANTINE
    assert payload["src_ip"] == "192.168.1.50"
    assert payload["action"] == "drop"
    assert payload["protocol"] == "TCP"

@pytest.mark.asyncio
async def test_xai_rule_generator_rate_limit():
    shap_values = {"UDP_length": 0.8}
    severity = SeverityLevel.MEDIUM
    
    action, payload = XAIRuleGenerator.generate_sdn_rule("10.0.0.5", shap_values, severity)
    
    assert action == MitigationLevel.RATE_LIMIT
    assert payload["src_ip"] == "10.0.0.5"
    assert payload["rate"] == 100
    assert payload["protocol"] == "UDP"

@pytest.mark.asyncio
async def test_sdn_client_mocked(mocker):
    """Test pushing rule to mocked Ryu."""
    mocker.patch("httpx.AsyncClient.post", return_value=mocker.MagicMock(status_code=200))
    
    client = SDNClient()
    success = await client.push_rule({"src_ip": "1.2.3.4", "action": "drop"})
    
    assert success is True
