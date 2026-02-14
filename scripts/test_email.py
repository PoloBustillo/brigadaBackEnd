"""
Test script for email service.
Run: python scripts/test_email.py
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.email_service import email_service


async def test_activation_email():
    """Test sending activation code email."""
    print("🧪 Testing Resend Email Service\n")
    print("=" * 50)
    
    # Test data
    test_data = {
        "to_email": "test@example.com",  # Change this to your email for testing
        "full_name": "Juan Pérez González",
        "activation_code": "123456",
        "expires_in_hours": 72,
        "custom_message": "Bienvenido al equipo de Brigada. Tu supervisor es María García."
    }
    
    print(f"📧 Sending activation email to: {test_data['to_email']}")
    print(f"👤 Full name: {test_data['full_name']}")
    print(f"🔑 Activation code: {test_data['activation_code']}")
    print(f"⏰ Expires in: {test_data['expires_in_hours']} hours")
    print(f"💬 Custom message: {test_data['custom_message']}")
    print("\n" + "=" * 50)
    print("Sending email...\n")
    
    # Send email
    result = await email_service.send_activation_email(**test_data)
    
    # Display result
    if result["success"]:
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print(f"   Email ID: {result.get('email_id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print("\n📬 Check your inbox (and spam folder)")
        print("   View details in Resend dashboard: https://resend.com/logs")
    else:
        print("❌ EMAIL SEND FAILED!")
        print(f"   Error: {result.get('error')}")
        print(f"   Message: {result.get('message')}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check RESEND_API_KEY in .env file")
        print("   2. Verify domain is configured in Resend")
        print("   3. Check Resend dashboard for errors")
    
    print("\n" + "=" * 50)
    return result


async def test_resend_email():
    """Test resending (reminder) email."""
    print("\n\n🔄 Testing Email Resend\n")
    print("=" * 50)
    
    test_data = {
        "to_email": "test@example.com",  # Change this to your email
        "full_name": "Juan Pérez González",
        "activation_code": "789012",
        "expires_in_hours": 48  # 2 days remaining
    }
    
    print(f"📧 Resending to: {test_data['to_email']}")
    print(f"⏰ Remaining time: {test_data['expires_in_hours']} hours")
    print("\n" + "=" * 50)
    print("Sending reminder email...\n")
    
    result = await email_service.resend_activation_email(**test_data)
    
    if result["success"]:
        print("✅ REMINDER EMAIL SENT!")
        print(f"   Email ID: {result.get('email_id')}")
    else:
        print("❌ REMINDER EMAIL FAILED!")
        print(f"   Error: {result.get('error')}")
    
    print("\n" + "=" * 50)
    return result


def main():
    """Run email tests."""
    print("\n" + "=" * 50)
    print("   BRIGADA EMAIL SERVICE TEST")
    print("=" * 50 + "\n")
    
    # Check environment
    from app.core.config import settings
    
    print("🔧 Configuration:")
    print(f"   FROM_EMAIL: {settings.FROM_EMAIL}")
    print(f"   FROM_NAME: {settings.FROM_NAME}")
    print(f"   RESEND_API_KEY: {'✅ Set' if settings.RESEND_API_KEY else '❌ Not set'}")
    print(f"   ENVIRONMENT: {settings.ENVIRONMENT}")
    
    if not settings.RESEND_API_KEY:
        print("\n❌ ERROR: RESEND_API_KEY not configured in .env file")
        print("   Please add: RESEND_API_KEY=re_your_key_here")
        return
    
    # Run tests
    loop = asyncio.get_event_loop()
    
    # Test 1: Standard activation email
    result1 = loop.run_until_complete(test_activation_email())
    
    # Test 2: Resend/reminder email
    result2 = loop.run_until_complete(test_resend_email())
    
    # Summary
    print("\n\n" + "=" * 50)
    print("   TEST SUMMARY")
    print("=" * 50)
    print(f"Activation Email: {'✅ Success' if result1['success'] else '❌ Failed'}")
    print(f"Reminder Email: {'✅ Success' if result2['success'] else '❌ Failed'}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
