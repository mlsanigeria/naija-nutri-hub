import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from auth.mail import send_email_welcome

def test_send_welcome_email():
    """
    Test sending the welcome email using the implemented send_email_welcome function.
    Ensure your .env file has correct credentials before running.
    """

    result = send_email_welcome(
        subject="🎉 Welcome to Naija Nutri Hub!",
        body={
            "user_name": "John Doe",
            "app_name": "Naija Nutri Hub",
            "dashboard_url": "https://naijanutrihub.com/dashboard",
            "support_email": "support@naijanutrihub.com"
        },
        receiver="example@gmail.com"  # Replace with a valid email for testing
    )

    print(result)  # Print to verify output manually

    # Optional: simple assertion for pytest
    assert result["status"] == "success", f"Email sending failed: {result}"

if __name__ == "__main__":
    test_send_welcome_email()
