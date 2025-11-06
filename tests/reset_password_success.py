import sys
from pathlib import Path

# Add the project root (naija-nutri-hub) to PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))

from auth.mail import send_email_reset_password_success


def test_send_reset_password_success_email():
    """
    Test sending the Password Reset Success email using the implemented
    send_email_reset_password_success function.
    Ensure your .env file has valid SMTP credentials before running.
    """

    result = send_email_reset_password_success(
    user_firstname="John",
    receiver="example@gmail.com"
    )

    print(result)  # Output for manual verification

    # Optional assertion for pytest-based automated testing
    assert result["status"] == "success", f"Email sending failed: {result}"

if __name__ == "__main__":
    test_send_reset_password_success_email()
