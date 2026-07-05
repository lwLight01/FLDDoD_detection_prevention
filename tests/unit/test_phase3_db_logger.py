"""
tests/unit/test_phase3_db_logger.py
-----------------------------------
Unit tests for DB Checkpointing & Logging (Milestone 20).

Tests:
  - Verify FLRound creation.
  - Verify FLClientUpdate creation.
"""

import pytest
from datetime import datetime
from src.fl_server.db_logger import log_round_start, log_client_updates, log_round_completion
from src.mitigation_engine.db.models import FLRound, FLClient, FLClientUpdate
from src.fl_server.db_logger import SessionLocal

@pytest.fixture
def db_session():
    # In a real environment we would use a mock DB or test DB, but for now we'll just test
    # the functions run. We should ideally mock the Session to avoid writing to the actual dev DB.
    # We will use unittest.mock for this.
    pass

def test_log_round_start_mocked(mocker):
    # Mock the DB session
    mock_session = mocker.patch("src.fl_server.db_logger.SessionLocal")
    mock_db = mock_session.return_value.__enter__.return_value
    
    # Mock the FLRound object that gets added
    mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

    round_id = log_round_start("v1.0-test")
    
    # Assert session was created and add/commit were called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert round_id == 1
    
    added_obj = mock_db.add.call_args[0][0]
    assert isinstance(added_obj, FLRound)
    assert added_obj.model_version_tag == "v1.0-test"

def test_log_client_updates_mocked(mocker):
    mock_session = mocker.patch("src.fl_server.db_logger.SessionLocal")
    mock_db = mock_session.return_value.__enter__.return_value
    
    # Return None for query.first() so it creates a new client
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', "mock_uuid")

    updates = [{
        "cid": "client_X",
        "cosine_similarity": 0.95,
        "assigned_trust_weight": 200.0,
        "accepted": True
    }]
    
    log_client_updates(1, updates)
    
    # It should add a Client and a ClientUpdate
    assert mock_db.add.call_count == 2
    assert mock_db.commit.call_count == 2
    
    # Check the update record
    update_obj = mock_db.add.call_args[0][0]
    assert isinstance(update_obj, FLClientUpdate)
    assert update_obj.round_id == 1
    assert update_obj.cosine_similarity == 0.95
    assert update_obj.assigned_trust_weight == 200.0

def test_log_round_completion_mocked(mocker):
    mock_session = mocker.patch("src.fl_server.db_logger.SessionLocal")
    mock_db = mock_session.return_value.__enter__.return_value
    
    # Mock returning an existing FLRound
    mock_round = FLRound(id=1, model_version_tag="test")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_round
    
    log_round_completion(1, global_loss=0.5, global_accuracy=0.92)
    
    mock_db.commit.assert_called_once()
    assert mock_round.end_time is not None
    assert mock_round.global_loss == 0.5
    assert mock_round.global_accuracy == 0.92
