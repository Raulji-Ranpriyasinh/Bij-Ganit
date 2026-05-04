"""PDF generation service using WeasyPrint (Sprint 6 - Task 6.1).

This service renders Jinja2 HTML templates with provided context data
and converts them to PDF bytes using WeasyPrint.
"""

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    raise ImportError(
        "WeasyPrint is required for PDF generation. "
        "Install it with: pip install weasyprint"
    )


# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "pdf"


def get_jinja_env() -> Environment:
    """Create and configure Jinja2 environment for PDF templates."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(template_name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 template with the given context.
    
    Args:
        template_name: Name of the template file (e.g., 'invoice/invoice1.html')
        context: Dictionary of variables to pass to the template
        
    Returns:
        Rendered HTML string
    """
    env = get_jinja_env()
    template = env.get_template(template_name)
    return template.render(**context)


def generate_pdf(template_name: str, context: dict[str, Any]) -> bytes:
    """Generate PDF bytes from a Jinja2 HTML template.
    
    Args:
        template_name: Name of the template file (e.g., 'invoice/invoice1.html')
        context: Dictionary of variables to pass to the template
        
    Returns:
        PDF file as bytes
    """
    # Render the HTML template
    html_content = render_template(template_name, context)
    
    # Configure fonts for WeasyPrint
    font_config = FontConfiguration()
    
    # Create CSS for custom fonts if needed
    css = CSS(string="""
        @page {
            size: A4;
            margin: 0;
        }
    """, font_config=font_config)
    
    # Generate PDF
    pdf = HTML(string=html_content).write_pdf(stylesheets=[css], font_config=font_config)
    
    return pdf


def generate_pdf_to_file(template_name: str, context: dict[str, Any], output_path: str | Path) -> None:
    """Generate PDF and save to disk.
    
    Args:
        template_name: Name of the template file
        context: Dictionary of variables to pass to the template
        output_path: Path where the PDF will be saved
    """
    pdf_bytes = generate_pdf(template_name, context)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)


def get_available_templates(category: str) -> list[dict[str, str]]:
    """Get list of available templates for a category.
    
    Args:
        category: Template category ('invoice', 'estimate', 'payment')
        
    Returns:
        List of dicts with template name and preview path
    """
    category_dir = TEMPLATES_DIR / category
    if not category_dir.exists():
        return []
    
    templates = []
    for file in sorted(category_dir.glob("*.html")):
        template_name = file.stem  # e.g., 'invoice1'
        preview_path = f"/static/previews/{category}/{template_name}.png"
        templates.append({
            "name": template_name,
            "display_name": f"Template {template_name[-1]}",  # e.g., 'Template 1'
            "preview_url": preview_path,
            "path": f"{category}/{file.name}"
        })
    
    return templates
