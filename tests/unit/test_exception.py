import sys
import pytest
from src.utils.exception import CustomException, error_message_detail


def test_error_message_detail():
    try:
        raise ValueError("test error")
    except ValueError as e:
        msg = error_message_detail(e, sys)
        assert "test_exception.py" in msg
        assert "line number" in msg
        assert "test error" in msg


def test_custom_exception():
    try:
        raise ValueError("inner error")
    except ValueError as e:
        ce = CustomException(e, sys)
        assert "inner error" in str(ce)
        assert ce.detailed_message == str(ce)


def test_error_message_detail_no_traceback():
    # Mocking a scenario where traceback is None
    class MockSys:
        def exc_info(self):
            return None, None, None

    msg = error_message_detail("simple error", MockSys())
    assert "unknown" in msg
    assert "line number: [0]" in msg
