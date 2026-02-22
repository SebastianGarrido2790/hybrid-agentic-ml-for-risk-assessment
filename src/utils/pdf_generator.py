import markdown
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from datetime import datetime
from pathlib import Path


def generate_pdf_report(report_md: str, filename: str = "risk_report.pdf") -> str:
    """
    Converts the markdown assessment report into a professional PDF file using xhtml2pdf.
    This approach is highly portable and doesn't require system-level GTK dependencies.
    """
    try:
        # Define paths
        base_dir = Path(__file__).resolve().parent.parent.parent
        template_dir = base_dir / "src" / "utils" / "templates"
        output_dir = base_dir / "reports" / "figures"
        output_dir.mkdir(exist_ok=True)

        # 1. Convert Markdown to HTML
        # We use 'extra' for tables and 'nl2br' for better paragraph handling
        report_html_content = markdown.markdown(
            report_md, extensions=["extra", "smarty", "nl2br"]
        )

        # 2. Setup Jinja2 Environment
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("report_template.html")

        # 3. Render Template
        company_id = "N/A"
        if "_" in filename:
            parts = filename.split("_")
            if len(parts) >= 3:
                company_id = parts[-1].replace(".pdf", "")

        render_data = {
            "company_id": company_id,
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "report_content_html": report_html_content,
        }

        final_html = template.render(render_data)

        # 4. Generate PDF
        output_path = output_dir / filename
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(final_html, dest=pdf_file)

        if pisa_status.err:
            print(f"xhtml2pdf Error during rendering: {pisa_status.err}")

        return str(output_path)

    except Exception as e:
        print(f"PDF Generation Error: {e}")
        raise e
