"""
Unit tests for telemetry configuration.
"""

import os
from unittest.mock import patch

from src.utils.telemetry import configure_tracer


def test_configure_tracer_basic():
    """Test tracer configuration with defaults."""
    with (
        patch("src.utils.telemetry.OTLPSpanExporter"),
        patch("src.utils.telemetry.BatchSpanProcessor"),
        patch("src.utils.telemetry.TracerProvider") as mock_provider,
    ):
        tracer = configure_tracer("test-service", "test-env")
        assert tracer is not None
        mock_provider.assert_called_once()


def test_configure_tracer_debug_mode():
    """Test tracer configuration with debug mode enabled."""
    with (
        patch.dict(os.environ, {"DEBUG_TELEMETRY": "1"}),
        patch("src.utils.telemetry.OTLPSpanExporter"),
        patch("src.utils.telemetry.ConsoleSpanExporter") as mock_console,
        patch("src.utils.telemetry.BatchSpanProcessor"),
        patch("src.utils.telemetry.TracerProvider"),
    ):
        configure_tracer()
        mock_console.assert_called_once()
