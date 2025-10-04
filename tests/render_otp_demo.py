"""
Simple demo to render the OTP HTML template with sample data.

Generates two files:
 - rendered_desktop.html (full-width rendering)
 - rendered_mobile.html  (narrow viewport emulation)

Usage:
    python render_otp_demo.py

This script performs simple placeholder replacement and writes the results.
It does not depend on external templating engines so it's safe for quick checks.
"""
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / 'auth' / 'html_email_themes' / 'otp_request.html'
OUT_DESKTOP = Path(__file__).with_name('rendered_desktop.html')
OUT_MOBILE = Path(__file__).with_name('rendered_mobile.html')

SAMPLE = {
    'otp': '123456',
    'expiry_minutes': 10,
    'user_name': 'John Doe',
    'app_name': 'Naija Nutri Hub',
    'support_email': 'support@naijanutri.example',
}


def render_template(text: str, context: dict) -> str:
    out = text
    for key, val in context.items():
        out = out.replace('{{' + key + '}}', str(val))
    return out


def main():
    if not TEMPLATE.exists():
        print('Template not found:', TEMPLATE)
        return

    html = TEMPLATE.read_text(encoding='utf-8')
    rendered = render_template(html, SAMPLE)

    # Desktop output (straight write)
    OUT_DESKTOP.write_text(rendered, encoding='utf-8')
    print('Wrote', OUT_DESKTOP)

    # Mobile output: wrap with a narrow container to emulate mobile preview
    mobile_wrapper = '\n'.join([
        '<!doctype html>',
        '<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>Mobile preview</title>',
        '<style>body{margin:0;padding:12px;background:#efefef}.preview{max-width:360px;margin:0 auto;border:1px solid #282828}</style>',
        '</head><body><div class="preview">',
        rendered,
        '</div></body></html>'
    ])

    OUT_MOBILE.write_text(mobile_wrapper, encoding='utf-8')
    print('Wrote', OUT_MOBILE)


if __name__ == '__main__':
    main()
