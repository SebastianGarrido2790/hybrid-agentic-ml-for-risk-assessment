"""
Unit tests for pdf_generator.py.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.utils.pdf_generator import generate_pdf_report


def test_generate_pdf_report_success():
    """Test PDF generation from markdown."""
    report_md = "# Test Report\nThis is a test."
    filename = "ACRAS_Report_123.pdf"

    # We don't want to actually run pisa if we can avoid it, or we can let it run
    # to verify the integration. Let's try running it first.
    try:
        pdf_bytes = generate_pdf_report(report_md, filename)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
    except Exception as e:
        pytest.fail(f"PDF generation failed: {e}")


def test_generate_pdf_report_save_to_disk():
    """Test PDF generation and saving to disk."""
    report_md = "# Test Report\nThis is a test."
    filename = "ACRAS_Report_456.pdf"

    # Patch ONLY the open call in src.utils.pdf_generator
    with patch("src.utils.pdf_generator.open", MagicMock()) as mock_open:
        pdf_bytes = generate_pdf_report(report_md, filename, save_to_disk=True)
        assert isinstance(pdf_bytes, bytes)
        mock_open.assert_called()


def test_generate_pdf_report_filename_parsing():
    """Test company ID extraction from filename."""
    report_md = "# Test Report"

    # We check the internal logic by mocking the template render
    with patch("src.utils.pdf_generator.Environment") as mock_env_class:
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env
        mock_template = MagicMock()
        mock_template.render.return_value = "<html><body>Test</body></html>"
        mock_env.get_template.return_value = mock_template

        generate_pdf_report(report_md, "ACRAS_Report_789_gemini.pdf")

        # Check if company_id 789 was passed to template
        args, kwargs = mock_template.render.call_args
        # In the current implementation, it's passed as a single positional dict
        assert args[0]["company_id"] == "789"
