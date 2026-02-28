"""
PDF Generation Utility for ACRAS.

This module provides functionality to convert markdown-based risk assessment reports
into professional PDF documents using xhtml2pdf and Jinja2 templates.
The generator uses an in-memory approach (returning bytes) to optimize performance
and prevent unnecessary disk I/O in the Streamlit application.
"""

import markdown
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from datetime import datetime
from pathlib import Path
import io


def generate_pdf_report(
    report_md: str, filename: str = "risk_report.pdf", save_to_disk: bool = False
) -> bytes:
    """
    Converts a markdown assessment report into a professional PDF file.

    This function uses a memory-efficient approach by rendering the PDF into a
    byte stream (io.BytesIO) instead of writing directly to a file. This is
    ideal for web environments where the file is intended for immediate download.

    Args:
        report_md (str): The raw markdown content of the generated report.
        filename (str, optional): The base filename for the report. Used to extract
            metadata like Company ID. Defaults to "risk_report.pdf".
        save_to_disk (bool, optional): If True, also persists a copy of the PDF
            to the system's 'reports/figures' directory. Defaults to False.

    Returns:
        bytes: The raw PDF binary data, ready to be sent to a browser or saved.

    Raises:
        Exception: If the PDF rendering engine (xhtml2pdf) encounters an error.
    """
    try:
        # Define paths
        base_dir = Path(__file__).resolve().parent.parent.parent
        template_dir = base_dir / "src" / "utils" / "templates"

        # 1. Convert Markdown to HTML
        report_html_content = markdown.markdown(
            report_md, extensions=["extra", "smarty", "nl2br"]
        )

        # 2. Setup Jinja2 Environment
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("report_template.html")

        # 3. Render Template
        company_id = "N/A"
        if "_" in filename:
            # Handle formats like ACRAS_Report_233.pdf or ACRAS_Report_233_gemini.pdf
            clean_name = filename.replace(".pdf", "")
            parts = [p for p in clean_name.split("_") if p]
            if len(parts) >= 3:
                # The ID is typically the third part in "ACRAS_Report_123_..."
                # We prioritize the first numerical part we find after prefix
                for p in parts[2:]:
                    if p.isdigit():
                        company_id = p
                        break
                if company_id == "N/A":
                    # Fallback to the part before provider nick or last part
                    company_id = parts[-2] if len(parts) >= 4 else parts[-1]

        render_data = {
            "company_id": company_id,
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "report_content_html": report_html_content,
        }

        final_html = template.render(render_data)

        # 4. Generate PDF in memory
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(final_html, dest=pdf_buffer)

        if pisa_status.err:
            print(f"xhtml2pdf Error during rendering: {pisa_status.err}")
            raise Exception(f"PDF Rendering Error: {pisa_status.err}")

        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        # 5. Optional: Save to disk (for internal tracking if needed)
        if save_to_disk:
            output_dir = base_dir / "reports" / "figures"
            output_dir.mkdir(exist_ok=True, parents=True)
            output_path = output_dir / filename
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            print(f"Report saved to {output_path}")

        return pdf_bytes

    except Exception as e:
        print(f"PDF Generation Error: {e}")
        raise e
