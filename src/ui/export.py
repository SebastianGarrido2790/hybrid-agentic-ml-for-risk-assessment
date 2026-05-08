"""
PDF Generation and Export Logic for the ACRAS UI.

This module encapsulates the logic for constructing filenames and rendering
the executive report download interface.
"""

from typing import cast

import streamlit as st

from src.utils.pdf_generator import generate_pdf_report


def prepare_pdf_export(
    assessment_result: str, company_id: str, provider: str, used_fallback_lite: bool
) -> bytes | None:
    """
    Generate PDF bytes from the assessment result.

    Args:
        assessment_result: The markdown content of the final report.
        company_id: The ID of the assessed entity.
        provider: The name of the primary LLM provider.
        used_fallback_lite: Whether a fallback model was used during generation.

    Returns:
        Optional[bytes]: The generated PDF content, or None if generation failed.
    """
    try:
        provider_nick = provider.lower()
        if used_fallback_lite:
            provider_nick += "-lite"

        filename = f"ACRAS_Report_{company_id}_{provider_nick}.pdf"

        pdf_bytes = generate_pdf_report(
            assessment_result,
            filename=filename,
            save_to_disk=True,
        )
        return cast(bytes, pdf_bytes)
    except Exception as e:
        st.error(f"PDF Preparation Error: {e}")
        return None


def render_download_section(
    pdf_bytes: bytes | None, company_id: str, provider: str, used_fallback_lite: bool
) -> None:
    """
    Render the download button component in the UI.

    Args:
        pdf_bytes: The generated PDF content.
        company_id: The ID of the assessed entity.
        provider: The name of the primary LLM provider.
        used_fallback_lite: Whether a fallback model was used.
    """
    st.markdown("---")
    if pdf_bytes:
        provider_nick = provider.lower()
        if used_fallback_lite:
            provider_nick += "-lite"

        st.download_button(
            label="📥 Download Executive PDF",
            data=pdf_bytes,
            file_name=f"ACRAS_Report_{company_id}_{provider_nick}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.warning("⚠️ Report preparation partial. PDF not available.")
