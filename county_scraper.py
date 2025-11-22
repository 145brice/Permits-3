#!/usr/bin/env python3
"""
Development helper - Quick commands for testing
"""
import sys
import os

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# --- SENDGRID EMAIL FUNCTION & EXAMPLES ---
import requests

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')  # Set this in your .env file
SENDGRID_FROM = os.getenv('FROM_EMAIL', 'your_verified_sender@yourdomain.com')
SENDGRID_TEMPLATE_ID = 'permitspython'  # Your dynamic template ID

def send_sendgrid_email(to_email, dynamic_template_data, template_id=SENDGRID_TEMPLATE_ID, subject=None):
    """
    Send an email using SendGrid dynamic templates.
    Args:
        to_email (str): Recipient email address
        dynamic_template_data (dict): Data for template variables
        template_id (str): SendGrid dynamic template ID
        subject (str): Optional subject override
    Returns: True if sent, False otherwise
    """
    if not SENDGRID_API_KEY:
        print("❌ SENDGRID_API_KEY not set!")
        return False
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "dynamic_template_data": dynamic_template_data
            }
        ],
        "from": {"email": SENDGRID_FROM},
        "template_id": template_id
    }
    if subject:
        payload["subject"] = subject
    resp = requests.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
    if resp.status_code == 202:
        print(f"✅ Email sent to {to_email}")
        return True
    else:
        print(f"❌ Failed to send email: {resp.status_code} {resp.text}")
        return False

# --- EXAMPLE 1: ADMIN PURCHASE NOTIFICATION ---
# Copy-paste this where you handle new purchases (e.g., Stripe webhook)
# send_sendgrid_email(
#     to_email="145brice@gmail.com",
#     dynamic_template_data={
#         "headline": "New subscriber! John Doe just paid $49.99 for Nashville",
#         "subscriber_name": "John Doe",
#         "product": "Nashville",
#         "amount": "$49.99",
#         "stripe_id": "sub_abc123"
#     }
# )

# --- EXAMPLE 2: ADMIN Q&A / CONTACT FORM NOTIFICATION ---
# Copy-paste this where you handle contact form submissions
# send_sendgrid_email(
#     to_email="145brice@gmail.com",
#     dynamic_template_data={
#         "headline": "New message from john@buildpro.com",
#         "subject": "Can I add Austin?",
#         "message": "Hey, can I get Austin leads?",
#         "from_email": "john@buildpro.com"
#     }
# )

# --- EXAMPLE 3: CUSTOMER DAILY PERMIT EMAIL ---
# Copy-paste this in your daily job for each customer
# send_sendgrid_email(
#     to_email="customer@email.com",
#     dynamic_template_data={
#         "headline": "Hey John, here are today’s 3 Nashville permits…",
#         "permit_count": 3,
#         "permits": [
#             {"address": "120K kitchen add on Oak St."},
#             {"address": "200K bath remodel on Main St."},
#             {"address": "New ADU on 5th Ave."}
#         ],
#         "city": "Nashville"
#     }
# )
# --- END SENDGRID EMAIL EXAMPLES ---

def print_menu():
    print("\n" + "="*50)
    print("🏗️  CONTRACTOR LEADS - DEV MENU")
    print("="*50)
    print("\n1. Test Scrapers")
    print("2. Test AI Scorer")
    print("3. Test Email Service")
    print("4. Run Manual Job (Full Pipeline)")
    print("5. Test Database Connection")
    print("6. Check Environment Setup")
    print("7. Start Flask App")
    print("8. Start Scheduler")
    print("9. Run All Tests")
    print("0. Exit")
    print("\n" + "="*50)

def test_scrapers():
    print("\n🕷️  Testing Scrapers...")
    try:
        from county_permits_scraper import CountyPermitScraper
        scraper = CountyPermitScraper()
        scraper.run_all()
        print("\n✅ Scrapers completed successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_scorer():
    print("\n🤖 Testing AI Scorer...")
    try:
        from ai_scorer import LeadScorer
        scorer = LeadScorer()
        
        test_permit = {
            'county': 'Nashville-Davidson',
            'permit_number': 'TEST-001',
            'address': '123 Broadway, Nashville, TN',
            'permit_type': 'New Construction - Commercial',
            'estimated_value': 250000,
            'work_description': 'New office building construction project'
        }
        
        scored = scorer.score_permit(test_permit)
        print(f"\n✅ Scoring successful!")
        print(f"Score: {scored['score']}/100")
        print(f"Breakdown: {scored['score_breakdown']}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_email():
    print("\n📧 Testing Email Service...")
    to_email = input("Enter test email address: ")
    
    # Use the existing, working function from the top of the script
    success = send_sendgrid_email(
        to_email=to_email,
        dynamic_template_data={
            "headline": "Test from Dev Menu",
            "subject": "System Test - Option 3",
            "message": "This email confirms your SendGrid service is configured.",
            "from_email": SENDGRID_FROM
        },
        subject="Dev Menu Email Test"
    )
    
    if success:
        print("\n✅ Test email successfully initiated!")
    else:
        print("\n❌ Failed to send test email. Check API key and logs.")

def run_manual_job():
    print("\n🚀 Running Manual Job...")
    confirm = input("This will scrape, score, and email. Continue? (y/n): ")
    
    if confirm.lower() == 'y':
        try:
            from scheduler import LeadScheduler
            scheduler = LeadScheduler()
            scheduler.run_nightly_job()
            print("\n✅ Job completed!")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_database():
    print("\n🔥 Testing Firebase Connection...")
    try:
        from firebase_backend import FirebaseBackend
        backend = FirebaseBackend()
        print("✅ Firebase connected!")
        
        # Test read
        permits = backend.get_recent_permits(days=1)
        print(f"✅ Found {len(permits)} recent permits in database")
    except Exception as e:
        print(f"❌ Error: {e}")

def check_environment():
    print("\n⚙️  Checking Environment Setup...")
    
    # Check .env
    if os.path.exists('.env'):
        print("✅ .env file exists")
    else:
        print("❌ .env file missing")
    
    # Check firebase credentials
    if os.path.exists('firebase-credentials.json'):
        print("✅ firebase-credentials.json exists")
    else:
        print("❌ firebase-credentials.json missing")
    
    # Check imports
    packages = [
        'requests', 'bs4', 'transformers', 'firebase_admin',
        'stripe', 'flask', 'reportlab', 'schedule'
    ]
    
    print("\nPackage check:")
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Run: pip install -r requirements.txt")

def start_flask():
    print("\n🌐 Starting Flask App...")
    os.system('python app.py')

def start_scheduler():
    print("\n⏰ Starting Scheduler...")
    os.system('python scheduler.py')

def run_all_tests():
    print("\n🧪 Running All Tests...")
    os.system('python test_setup.py')

def main():
    while True:
        print_menu()
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == '1':
            test_scrapers()
        elif choice == '2':
            test_scorer()
        elif choice == '3':
            test_email()
        elif choice == '4':
            run_manual_job()
        elif choice == '5':
            test_database()
        elif choice == '6':
            check_environment()
        elif choice == '7':
            start_flask()
        elif choice == '8':
            start_scheduler()
        elif choice == '9':
            run_all_tests()
        elif choice == '0':
            print("\n👋 Goodbye!")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    # --- TEMP: SENDGRID EMAIL TESTS ---
    print("\n🔧 Running SendGrid Email Tests...")
    print("="*50)
    
    # Check if API key exists first
    if not SENDGRID_API_KEY:
        print("❌ ERROR: SENDGRID_API_KEY not found in .env file!")
        print("📝 Add this to your .env file:")
        print("   SENDGRID_API_KEY=your_sendgrid_api_key_here")
        print("   SENDGRID_FROM=your_verified_sender@yourdomain.com")
        print("\n")
    else:
        print(f"✅ API Key found: {SENDGRID_API_KEY[:8]}...")
        print(f"✅ From email: {SENDGRID_FROM}\n")
        
        # 1. Admin purchase notification
        print("📧 Test 1: Admin purchase notification...")
        send_sendgrid_email(
            to_email="145brice@gmail.com",
            dynamic_template_data={
                "headline": "New subscriber! John Doe just paid $49.99 for Nashville",
                "subscriber_name": "John Doe",
                "product": "Nashville",
                "amount": "$49.99",
                "stripe_id": "sub_abc123"
            }
        )

        # 2. Admin Q&A/contact form notification
        print("\n📧 Test 2: Admin Q&A notification...")
        send_sendgrid_email(
            to_email="145brice@gmail.com",
            dynamic_template_data={
                "headline": "New message from john@buildpro.com",
                "subject": "Can I add Austin?",
                "message": "Hey, can I get Austin leads?",
                "from_email": "john@buildpro.com"
            }
        )

        # 3. Customer daily permit email
        print("\n📧 Test 3: Customer daily permit email...")
        send_sendgrid_email(
            to_email="customer@email.com",
            dynamic_template_data={
                "headline": "Hey John, here are today's 3 Nashville permits…",
                "permit_count": 3,
                "permits": [
                    {"address": "120K kitchen add on Oak St."},
                    {"address": "200K bath remodel on Main St."},
                    {"address": "New ADU on 5th Ave."}
                ],
                "city": "Nashville"
            }
        )
    
    print("\n" + "="*50)
    input("Press Enter to continue to main menu...")

    main()
