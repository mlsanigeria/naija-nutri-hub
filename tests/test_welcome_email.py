from jinja2 import Template

def test_render_email():
    # Read the HTML template
    with open("auth/html_email_themes/onboarding.html", "r", encoding="utf-8") as f:
        template = Template(f.read())
    
    data = {
        "user_name": "John Doe",
        "get_started_link": "https://naija-nutri-hub.com/start",
        "app_name": "Naija-Nutri-Hub",
        "support_email": "support@naijanutrihub.com",
        "team_signature": "The Naija-Nutri-Hub Team"
    }

    html = template.render(**data)

    with open("auth/html_email_themes/welcome_preview.html", "w", encoding="utf-8") as out:
        out.write(html)

    print("✅ Email rendered successfully — check 'welcome_preview.html'")

if __name__ == "__main__":
    test_render_email()
