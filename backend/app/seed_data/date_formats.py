"""Static date-format dropdown values served by GET /api/v1/date/formats.

Each entry exposes:
* `carbon_format`  — the PHP-style format used by the reference Laravel app
  (kept for API compatibility so the frontend can stay the same).
* `moment_format`  — the corresponding moment.js / dayjs format string the
  React UI uses for rendering.
* `display`        — a sample rendering to show in the dropdown.
"""

DATE_FORMATS: list[dict] = [
    {"carbon_format": "Y/m/d", "moment_format": "YYYY/MM/DD", "display": "2025/12/31"},
    {"carbon_format": "Y-m-d", "moment_format": "YYYY-MM-DD", "display": "2025-12-31"},
    {"carbon_format": "d/m/Y", "moment_format": "DD/MM/YYYY", "display": "31/12/2025"},
    {"carbon_format": "d-m-Y", "moment_format": "DD-MM-YYYY", "display": "31-12-2025"},
    {"carbon_format": "m/d/Y", "moment_format": "MM/DD/YYYY", "display": "12/31/2025"},
    {"carbon_format": "M j, Y", "moment_format": "MMM D, YYYY", "display": "Dec 31, 2025"},
    {"carbon_format": "j M Y", "moment_format": "D MMM YYYY", "display": "31 Dec 2025"},
    {"carbon_format": "F j, Y", "moment_format": "MMMM D, YYYY", "display": "December 31, 2025"},
]
