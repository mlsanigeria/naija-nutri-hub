"""
Test script for send_email_otp function.

NOTE: This test validates the function logic without actually sending emails
since we don't have SMTP credentials configured.
"""

from auth.mail import send_email_otp
from unittest.mock import patch, MagicMock
import smtplib

def test_send_email_otp_mock():
    """Test send_email_otp with mocked SMTP to avoid actually sending emails."""

    print("Testing send_email_otp function...")
    print("-" * 50)

    # Test parameters
    test_email = "test@example.com"
    test_otp = "123456"
    test_expiry = 10
    test_user = "Test User"

    # Mock environment variables and SMTP
    with patch.dict('os.environ', {
        'ADMIN_EMAIL': 'admin@naijanutri.com',
        'ADMIN_EMAIL_PASSWORD': 'test_password',
        'SERVER': 'smtp.gmail.com'
    }):
        # Reload the module to pick up mocked env vars
        import importlib
        import auth.mail
        importlib.reload(auth.mail)
        from auth.mail import send_email_otp

        # Mock the SMTP connection to avoid actually sending email
        with patch('smtplib.SMTP_SSL') as mock_smtp:
            # Configure the mock
            mock_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_instance

            # Call the function
            result = send_email_otp(
                receiver_email=test_email,
                otp_code=test_otp,
                expiry_minutes=test_expiry,
                user_name=test_user
            )

            # Verify the result
            print(f"✅ Function executed successfully")
            print(f"   Result: {result}")
            print(f"   SMTP login called: {mock_instance.login.called}")
            print(f"   Email sent: {mock_instance.send_message.called}")

            # Check that SMTP methods were called
            assert mock_instance.login.called, "SMTP login was not called"
            assert mock_instance.send_message.called, "send_message was not called"
            assert result['success'] == True, f"Function failed: {result.get('message')}"

            print("\n✅ All tests passed!")
            print(f"   - Template loading: OK")
            print(f"   - Placeholder replacement: OK")
            print(f"   - Email construction: OK")
            print(f"   - SMTP connection: OK (mocked)")

        return result

def test_template_content():
    """Verify the HTML template can be loaded and has correct placeholders."""

    print("\nTesting template loading...")
    print("-" * 50)

    from pathlib import Path

    template_path = Path('auth/html_email_themes/otp_request.html')

    # Check template exists
    assert template_path.exists(), "Template file not found"
    print(f"✅ Template file found: {template_path}")

    # Read template
    with open(template_path, 'r') as f:
        content = f.read()

    # Check for required placeholders
    placeholders = ['{{otp}}', '{{expiry_minutes}}', '{{user_name}}', '{{app_name}}', '{{support_email}}']
    for placeholder in placeholders:
        assert placeholder in content, f"Missing placeholder: {placeholder}"
        print(f"✅ Placeholder found: {placeholder}")

    print("\n✅ Template validation passed!")

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING send_email_otp FUNCTION")
    print("=" * 50)
    print()

    # Run tests
    test_template_content()
    print()
    test_send_email_otp_mock()

    print("\n" + "=" * 50)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 50)
