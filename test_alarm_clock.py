import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import alarm_clock

@pytest.fixture(autouse=True)
def mock_storage(tmp_path):
    """
    Patch the ALARMS_FILE constant to use a temporary file.
    Ensures tests don't overwrite real user data.
    """
    test_file = tmp_path / "test_alarms.json"
    with patch("alarm_clock.ALARMS_FILE", test_file):
        yield

def test_load_save_alarms():
    """Test serialization and deserialization of the alarm store."""
    assert alarm_clock.load_alarms() == []
    
    mock_alarms = [
        {"id": "123", "time": "08:00", "label": "Morning", "recurring": True}
    ]
    alarm_clock.save_alarms(mock_alarms)
    
    loaded = alarm_clock.load_alarms()
    assert len(loaded) == 1
    assert loaded[0]["id"] == "123"

@patch("alarm_clock.sys.stdout")
@patch("alarm_clock.os.system")
@patch("alarm_clock.input")
@patch("alarm_clock.time.sleep")
def test_ring_dismiss_non_recurring(mock_sleep, mock_input, mock_system, mock_stdout):
    """Test dismissing a non-recurring alarm removes it from storage."""
    alarm = {"id": "1", "time": "09:00", "label": "Test", "recurring": False}
    alarm_clock.save_alarms([alarm])
    
    mock_input.return_value = "d"
    alarm_clock.ring(alarm)
    
    assert len(alarm_clock.load_alarms()) == 0

@patch("alarm_clock.sys.stdout")
@patch("alarm_clock.os.system")
@patch("alarm_clock.input")
@patch("alarm_clock.time.sleep")
def test_ring_dismiss_recurring(mock_sleep, mock_input, mock_system, mock_stdout):
    """Test dismissing a recurring alarm keeps it in storage."""
    alarm = {"id": "1", "time": "09:00", "label": "Test", "recurring": True}
    alarm_clock.save_alarms([alarm])
    
    mock_input.return_value = "d"
    alarm_clock.ring(alarm)
    
    assert len(alarm_clock.load_alarms()) == 1

@patch("alarm_clock.sys.stdout")
@patch("alarm_clock.os.system")
@patch("alarm_clock.input")
@patch("alarm_clock.time.sleep")
def test_ring_snooze(mock_sleep, mock_input, mock_system, mock_stdout):
    """Test snoozing mutates time."""
    alarm = {"id": "1", "time": "09:00", "label": "Test", "recurring": False}
    alarm_clock.save_alarms([alarm])
    
    mock_input.return_value = "s"
    alarm_clock.ring(alarm)
    
    alarms = alarm_clock.load_alarms()
    assert len(alarms) == 1
    assert alarms[0]["label"] == "Snoozed: Test"
    assert alarms[0]["time"] != "09:00"

def test_check_alarms_triggers_pending_rings():
    """Test the daemon check logic correctly queues alarms."""
    alarm = {"id": "1", "time": "09:00", "label": "Test", "recurring": False}
    alarm_clock.save_alarms([alarm])
    
    # Mock current time to match the alarm
    with patch("alarm_clock.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "09:00"
        
        # Reset global state
        alarm_clock._ringing_ids.clear()
        alarm_clock._pending_rings.clear()
        
        alarm_clock._check_alarms()
        
        assert len(alarm_clock._pending_rings) == 1
        assert alarm_clock._pending_rings[0]["id"] == "1"
