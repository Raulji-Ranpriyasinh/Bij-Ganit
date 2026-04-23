"""Static list of IANA timezones served by GET /api/v1/timezones.

Kept small and curated — covers the regions the reference Laravel app
advertises in its settings dropdown.  Add more here as customers need them;
the backend never reads from an external source.
"""

TIMEZONES: list[dict] = [
    {"key": "Pacific/Midway", "label": "(UTC-11:00) Midway Island"},
    {"key": "Pacific/Honolulu", "label": "(UTC-10:00) Hawaii"},
    {"key": "America/Anchorage", "label": "(UTC-09:00) Alaska"},
    {"key": "America/Los_Angeles", "label": "(UTC-08:00) Pacific Time (US & Canada)"},
    {"key": "America/Denver", "label": "(UTC-07:00) Mountain Time (US & Canada)"},
    {"key": "America/Chicago", "label": "(UTC-06:00) Central Time (US & Canada)"},
    {"key": "America/New_York", "label": "(UTC-05:00) Eastern Time (US & Canada)"},
    {"key": "America/Halifax", "label": "(UTC-04:00) Atlantic Time (Canada)"},
    {"key": "America/Sao_Paulo", "label": "(UTC-03:00) Brasilia"},
    {"key": "Atlantic/Azores", "label": "(UTC-01:00) Azores"},
    {"key": "UTC", "label": "(UTC+00:00) UTC"},
    {"key": "Europe/London", "label": "(UTC+00:00) London"},
    {"key": "Europe/Berlin", "label": "(UTC+01:00) Berlin, Paris, Madrid"},
    {"key": "Europe/Athens", "label": "(UTC+02:00) Athens, Cairo"},
    {"key": "Europe/Moscow", "label": "(UTC+03:00) Moscow"},
    {"key": "Asia/Dubai", "label": "(UTC+04:00) Dubai"},
    {"key": "Asia/Karachi", "label": "(UTC+05:00) Karachi"},
    {"key": "Asia/Kolkata", "label": "(UTC+05:30) Kolkata, Mumbai"},
    {"key": "Asia/Dhaka", "label": "(UTC+06:00) Dhaka"},
    {"key": "Asia/Bangkok", "label": "(UTC+07:00) Bangkok, Jakarta"},
    {"key": "Asia/Shanghai", "label": "(UTC+08:00) Beijing, Shanghai, Singapore"},
    {"key": "Asia/Tokyo", "label": "(UTC+09:00) Tokyo, Seoul"},
    {"key": "Australia/Sydney", "label": "(UTC+10:00) Sydney"},
    {"key": "Pacific/Auckland", "label": "(UTC+12:00) Auckland"},
]
