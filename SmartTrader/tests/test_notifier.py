"""
Tests for Notifier
"""
import pytest
from utils.notifier import Notifier

class TestNotifier:
    def test_initialization(self):
        n = Notifier()
        assert n.console_enabled == True
        assert n.email_enabled == False

    def test_send_console(self):
        n = Notifier()
        n.send("Test Subject", "Test Message", level="INFO")
        # Should not raise

    def test_notify_order(self):
        n = Notifier()
        n.notify_order("AAPL", "BUY", 150.0, 10)
        # Should not raise