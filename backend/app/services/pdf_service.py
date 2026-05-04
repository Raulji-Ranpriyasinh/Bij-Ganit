"""PDF generation service using WeasyPrint (Sprint 6).

This service accepts a Jinja2 HTML template path and context dict,
renders the template, and returns PDF bytes.
"""

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Try to import weasyprint; will fail if not installed
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


# Base directory for templates
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "pdf"


def get_jinja_env() -> Environment:
    """Create and return a Jinja2 environment configured for PDF templates."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generate_pdf(template_name: str, context: dict[str, Any]) -> bytes:
    """Generate PDF bytes from a Jinja2 template and context.
    
    Args:
        template_name: Name of the template file (e.g., "invoice/invoice1.html")
        context: Dictionary of variables to pass to the template
        
    Returns:
        PDF file as bytes
        
    Raises:
        ImportError: If WeasyPrint is not installed
        FileNotFoundError: If template doesn't exist
    """
    if not WEASYPRINT_AVAILABLE:
        raise ImportError(
            "WeasyPrint is not installed. Install it with: pip install weasyprint"
        )
    
    env = get_jinja_env()
    
    # Render the template
    template = env.get_template(template_name)
    html_content = template.render(**context)
    
    # Generate PDF using WeasyPrint
    html_obj = HTML(string=html_content, base_url=str(TEMPLATE_DIR))
    pdf_bytes = html_obj.write_pdf()
    
    return pdf_bytes


def generate_pdf_preview(template_name: str, context: dict[str, Any]) -> str:
    """Generate HTML preview from a Jinja2 template and context.
    
    Args:
        template_name: Name of the template file
        context: Dictionary of variables to pass to the template
        
    Returns:
        Rendered HTML string
    """
    env = get_jinja_env()
    template = env.get_template(template_name)
    return template.render(**context)


def list_templates(category: str = "invoice") -> list[dict[str, str]]:
    """List available templates for a given category.
    
    Args:
        category: Template category ("invoice", "estimate", or "payment")
        
    Returns:
        List of dicts with "name" and "preview" keys
    """
    category_dir = TEMPLATE_DIR / category
    if not category_dir.exists():
        return []
    
    templates = []
    for f in category_dir.glob("*.html"):
        name = f.stem  # e.g., "invoice1"
        templates.append({
            "name": name,
            "preview": f"/static/templates/{category}/{name}.png"
        })
    
    return templates


def save_pdf_to_disk(pdf_bytes: bytes, filepath: str | Path) -> None:
    """Save PDF bytes to disk.
    
    Args:
        pdf_bytes: PDF content as bytes
        filepath: Destination file path
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(pdf_bytes)
