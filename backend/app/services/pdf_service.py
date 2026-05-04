"""PDF generation service using WeasyPrint (Sprint 6 - Task 6.1).

This service renders Jinja2 HTML templates with context data and converts them to PDF bytes.
"""

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS


TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "pdf"


def _get_jinja_env() -> Environment:
    """Create Jinja2 environment pointing to PDF templates directory."""
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=False,
    )


def render_html(template_name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 template with the given context.
    
    Args:
        template_name: Name of the template file (e.g., 'invoice1.html')
        context: Dictionary of variables to pass to the template
        
    Returns:
        Rendered HTML string
    """
    env = _get_jinja_env()
    template = env.get_template(template_name)
    return template.render(**context)


def generate_pdf(template_name: str, context: dict[str, Any]) -> bytes:
    """Generate PDF bytes from a Jinja2 template and context.
    
    Args:
        template_name: Name of the template file (e.g., 'invoice1.html')
        context: Dictionary of variables to pass to the template
        
    Returns:
        PDF document as bytes
    """
    html_content = render_html(template_name, context)
    
    # Get the base URL for resolving relative assets
    base_path = TEMPLATE_DIR / template_name
    base_url = str(base_path.parent)
    
    # Create WeasyPrint HTML object and write PDF
    html = HTML(string=html_content, base_url=base_url)
    
    # Optional: Add default CSS for better rendering
    css = CSS(string="""
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 12px;
            line-height: 1.5;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
    """)
    
    pdf_bytes = html.write_pdf(stylesheets=[css])
    return pdf_bytes


def get_available_templates() -> list[dict[str, str]]:
    """Scan the templates directory and return available template names.
    
    Returns:
        List of dicts with 'name' and 'preview' keys
    """
    templates = []
    if TEMPLATE_DIR.exists():
        for file in TEMPLATE_DIR.glob("*.html"):
            name = file.stem  # filename without extension
            # Preview image path (placeholder - actual images would be stored separately)
            preview_path = f"/static/templates/pdf/{name}.png"
            templates.append({"name": name, "preview": preview_path})
    return templates
