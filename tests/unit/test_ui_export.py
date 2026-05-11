"""
Unit tests for UI Export utilities.
"""

from unittest.mock import patch

from src.ui.export import prepare_pdf_export, render_download_section


def test_prepare_pdf_export_success():
    """Test successful PDF preparation."""
    with patch("src.ui.export.generate_pdf_report") as mock_gen:
        mock_gen.return_value = b"fake-pdf-bytes"

        pdf_bytes = prepare_pdf_export("Result", "123", "Gemini", False)

        assert pdf_bytes == b"fake-pdf-bytes"
        mock_gen.assert_called_once()
        args, kwargs = mock_gen.call_args
        assert "123" in kwargs["filename"]
        assert "gemini" in kwargs["filename"]


def test_prepare_pdf_export_fallback():
    """Test PDF preparation with fallback model suffix."""
    with patch("src.ui.export.generate_pdf_report") as mock_gen:
        mock_gen.return_value = b"fake-pdf-bytes"

        prepare_pdf_export("Result", "456", "OpenAI", True)

        args, kwargs = mock_gen.call_args
        assert "openai-lite" in kwargs["filename"]


def test_render_download_section_success():
    """Test rendering download button when PDF is ready."""
    with (
        patch("streamlit.download_button") as mock_btn,
        patch("streamlit.markdown") as mock_md,
    ):
        render_download_section(b"pdf", "123", "Gemini", False)

        mock_btn.assert_called_once()
        mock_md.assert_called()


def test_render_download_section_missing():
    """Test rendering warning when PDF is missing."""
    with (
        patch("streamlit.warning") as mock_warn,
        patch("streamlit.markdown") as mock_md,
    ):
        render_download_section(None, "123", "Gemini", False)

        mock_warn.assert_called_once()
        mock_md.assert_called()
