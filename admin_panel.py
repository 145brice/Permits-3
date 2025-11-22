#!/usr/bin/env python3
"""
Admin Panel - Manage users, subscriptions, and view stats
Run with: python3 admin_panel.py
"""

import database
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def view_all_users():
    """Display all users"""
    print_header("👥 All Users")
    
    users = database.get_all_users()
    
    if not users:
        print("No users found.")
        return
    
    for user in users:
        print(f"ID: {user['id']}")
        print(f"Email: {user['email']}")
        print(f"Name: {user['full_name'] or 'N/A'}")
        print(f"Stripe ID: {user['stripe_customer_id'] or 'N/A'}")
        print(f"Created: {user['created_at']}")
        print(f"Last Login: {user['last_login'] or 'Never'}")
        print(f"Active: {'Yes' if user['is_active'] else 'No'}")
        print("-" * 60)

def view_subscription_stats():
    """Display subscription statistics"""
    print_header("📊 Subscription Statistics")
    
    stats = database.get_subscription_stats()
    
    print(f"Total Subscriptions: {stats['total_subscriptions']}")
    print(f"Active Subscriptions: {stats['active_subscriptions']}")
    print(f"Cancelled Subscriptions: {stats['cancelled_subscriptions']}")
    print(f"\nMonthly Recurring Revenue (MRR): ${stats['active_subscriptions'] * 49.99:.2f}")
    print(f"\nSubscriptions by County:")
    
    # Get breakdown by county
    with database.get_db() as conn:
        cursor = conn.execute("""
            SELECT state_key, county_key, COUNT(*) as count, status
            FROM subscriptions
            GROUP BY state_key, county_key, status
            ORDER BY state_key, county_key
        """)
        results = cursor.fetchall()
    
    current_state = None
    for row in results:
        if row['state_key'] != current_state:
            current_state = row['state_key']
            print(f"\n  {current_state.upper()}:")
        
        county_names = {
            'nashville': 'Nashville',
            'chattanooga': 'Chattanooga',
            'travis': 'Austin',
            'bexar': 'San Antonio'
        }
        county_display = county_names.get(row['county_key'], row['county_key'].title())
        print(f"    • {county_display}: {row['count']} ({row['status']})")

def view_user_details(user_id):
    """Display detailed info for a specific user"""
    print_header(f"🔍 User Details - ID {user_id}")
    
    user = database.get_user_by_id(user_id)
    if not user:
        print("❌ User not found")
        return
    
    print(f"Email: {user['email']}")
    print(f"Name: {user['full_name'] or 'N/A'}")
    print(f"Stripe Customer ID: {user['stripe_customer_id'] or 'N/A'}")
    print(f"Created: {user['created_at']}")
    print(f"Last Login: {user['last_login'] or 'Never'}")
    print(f"Active: {'Yes' if user['is_active'] else 'No'}")
    
    # Get subscriptions
    subscriptions = database.get_user_subscriptions(user_id)
    print(f"\nSubscriptions: {len(subscriptions)}")
    for sub in subscriptions:
        print(f"  • {sub['county_key'].title()}, {sub['state_key'].upper()}")
        print(f"    Status: {sub['status']}")
        print(f"    Started: {sub['started_at']}")
        if sub['cancelled_at']:
            print(f"    Cancelled: {sub['cancelled_at']}")
    
    # Get payments
    payments = database.get_user_payments(user_id)
    print(f"\nPayments: {len(payments)}")
    total_paid = sum(p['amount'] for p in payments)
    print(f"Total Paid: ${total_paid:.2f}")
    
    for payment in payments[:5]:  # Show last 5 payments
        print(f"  • ${payment['amount']:.2f} - {payment['status']} - {payment['created_at']}")

def create_test_subscription():
    """Create a test subscription for testing"""
    print_header("🧪 Create Test Subscription")
    
    email = input("Enter user email: ").strip()
    user = database.get_user_by_email(email)
    
    if not user:
        print(f"❌ User not found. Creating new user...")
        password = input("Enter password: ").strip()
        full_name = input("Enter full name (optional): ").strip() or None
        user_id = database.create_user(email, password, full_name)
        if user_id:
            user = database.get_user_by_id(user_id)
            print(f"✅ User created with ID {user_id}")
        else:
            print("❌ Failed to create user")
            return
    
    print(f"\nAvailable counties:")
    print("1. Nashville, TN (tennessee/nashville)")
    print("2. Chattanooga, TN (tennessee/chattanooga)")
    print("3. Austin, TX (texas/travis)")
    print("4. San Antonio, TX (texas/bexar)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    county_map = {
        '1': ('tennessee', 'nashville'),
        '2': ('tennessee', 'chattanooga'),
        '3': ('texas', 'travis'),
        '4': ('texas', 'bexar')
    }
    
    if choice not in county_map:
        print("❌ Invalid choice")
        return
    
    state_key, county_key = county_map[choice]
    
    # Create subscription
    stripe_sub_id = f"sub_test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    sub_id = database.create_subscription(user['id'], state_key, county_key, stripe_sub_id)
    
    if sub_id:
        print(f"\n✅ Test subscription created!")
        print(f"   User: {email}")
        print(f"   County: {county_key.title()}, {state_key.upper()}")
        print(f"   Subscription ID: {sub_id}")
    else:
        print("❌ Failed to create subscription")

def send_test_email():
    """Send a test email to a user"""
    print_header("📧 Send Test Email")
    
    email = input("Enter user email: ").strip()
    user = database.get_user_by_email(email)
    
    if not user:
        print("❌ User not found")
        return
    
    database.queue_email(
        user['id'],
        'test',
        'Test Email from Contractor Leads',
        'This is a test email to verify your email delivery is working.',
        datetime.now()
    )
    
    print(f"✅ Test email queued for {email}")
    print("Run the email_sender.py script to actually send it.")

def main_menu():
    """Display main menu and handle user input"""
    while True:
        print_header("🔧 Admin Panel")
        print("1. View All Users")
        print("2. View Subscription Stats")
        print("3. View User Details (by ID)")
        print("4. Create Test Subscription")
        print("5. Send Test Email")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            view_all_users()
        elif choice == '2':
            view_subscription_stats()
        elif choice == '3':
            user_id = input("Enter user ID: ").strip()
            try:
                view_user_details(int(user_id))
            except ValueError:
                print("❌ Invalid user ID")
        elif choice == '4':
            create_test_subscription()
        elif choice == '5':
            send_test_email()
        elif choice == '6':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("❌ Invalid choice")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    print("\n🚀 Contractor Leads Admin Panel")
    print("=" * 60)
    main_menu()
