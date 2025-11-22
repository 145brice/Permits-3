#!/usr/bin/env python3
"""
Email Sender - Sends daily contractor leads to subscribers
Run this daily via cron job at 6 AM
"""

import json
import os
from datetime import datetime
import database

# Email configuration - set these environment variables
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'leads@contractorleads.com')

def load_leads():
    """Load leads from database"""
    db_path = '/Users/briceleasure/Desktop/contractor-leads-saas/leads_db/current_leads.json'
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            return json.load(f).get('leads', {})
    return {}

def format_leads_html(leads, max_leads=50):
    """Format leads as HTML for email"""
    html = """
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <h2 style="color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 10px;">
            Today's Contractor Leads
        </h2>
        <p style="color: #666; margin-bottom: 30px;">
            {count} new leads • {date}
        </p>
    """.format(count=min(len(leads), max_leads), date=datetime.now().strftime('%B %d, %Y'))
    
    for i, lead in enumerate(leads[:max_leads]):
        address = lead.get('address', 'N/A')
        permit_type = lead.get('permit_type', 'N/A')
        date = lead.get('date', 'N/A')
        value = lead.get('estimated_value', 'N/A')
        score = lead.get('score', 0)
        description = lead.get('work_description', 'N/A')
        
        # Score color
        if score >= 85:
            score_color = '#22c55e'
        elif score >= 75:
            score_color = '#6366f1'
        else:
            score_color = '#fbbf24'
        
        html += f"""
        <div style="background: #f9fafb; border-left: 4px solid {score_color}; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #1f2937; font-size: 18px;">{address}</h3>
                <span style="background: {score_color}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px;">
                    {score}
                </span>
            </div>
            <p style="color: #6b7280; margin: 5px 0;"><strong>Type:</strong> {permit_type}</p>
            <p style="color: #6b7280; margin: 5px 0;"><strong>Date:</strong> {date}</p>
            <p style="color: #6b7280; margin: 5px 0;"><strong>Est. Value:</strong> {value}</p>
            <p style="color: #6b7280; margin: 5px 0;"><strong>Description:</strong> {description}</p>
        </div>
        """
    
    html += """
        <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 14px;">
                You're receiving this because you're subscribed to Contractor Leads.<br>
                <a href="http://localhost:8080/dashboard" style="color: #6366f1;">Manage Subscription</a>
            </p>
        </div>
    </div>
    """
    
    return html

def send_email_sendgrid(to_email, subject, html_content):
    """Send email using SendGrid API"""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content
        
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        from_email = Email(FROM_EMAIL)
        to_email = To(to_email)
        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email, subject, content)
        
        response = sg.client.mail.send.post(request_body=mail.get())
        
        if response.status_code in [200, 201, 202]:
            return True, None
        else:
            return False, f"SendGrid returned status {response.status_code}"
    
    except Exception as e:
        return False, str(e)

def send_daily_leads():
    """Main function to send daily leads to all active subscribers"""
    print(f"\n📧 Starting daily lead email delivery - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if SendGrid is configured
    if not SENDGRID_API_KEY:
        print("⚠️  SENDGRID_API_KEY not set. Set it with:")
        print("   export SENDGRID_API_KEY='your-api-key'")
        print("\n📝 Simulating email send (no actual emails sent)\n")
        use_sendgrid = False
    else:
        use_sendgrid = True
    
    # Load all leads
    all_leads = load_leads()
    
    # Get all active subscriptions
    with database.get_db() as conn:
        cursor = conn.execute("""
            SELECT s.*, u.email, u.full_name
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE s.status = 'active'
        """)
        subscriptions = cursor.fetchall()
    
    if not subscriptions:
        print("❌ No active subscriptions found")
        return
    
    print(f"Found {len(subscriptions)} active subscription(s)\n")
    
    sent_count = 0
    failed_count = 0
    
    for sub in subscriptions:
        state_key = sub['state_key']
        county_key = sub['county_key']
        email = sub['email']
        name = sub['full_name'] or 'Subscriber'
        
        # Get leads for this county
        county_leads = all_leads.get(state_key, {}).get(county_key, [])
        
        if not county_leads:
            print(f"⚠️  No leads for {county_key}, {state_key} - skipping {email}")
            continue
        
        # Format email
        county_names = {
            'nashville': 'Nashville, TN',
            'chattanooga': 'Chattanooga, TN',
            'travis': 'Austin, TX',
            'bexar': 'San Antonio, TX'
        }
        county_display = county_names.get(county_key, county_key.title())
        
        subject = f"🏗️ {len(county_leads)} New Leads in {county_display}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif;">
            <p>Hi {name},</p>
            <p>Here are today's contractor leads for <strong>{county_display}</strong>:</p>
        </div>
        """ + format_leads_html(county_leads)
        
        # Send email
        if use_sendgrid:
            success, error = send_email_sendgrid(email, subject, html_content)
            
            if success:
                print(f"✅ Sent {len(county_leads)} leads to {email} ({county_display})")
                
                # Record in email queue as sent
                database.queue_email(
                    sub['user_id'],
                    'daily_leads',
                    subject,
                    html_content[:500],  # Store truncated version
                    datetime.now()
                )
                with database.get_db() as conn:
                    conn.execute("""
                        UPDATE email_queue 
                        SET status = 'sent', sent_at = ?
                        WHERE user_id = ? AND email_type = 'daily_leads' 
                        AND status = 'pending'
                        ORDER BY created_at DESC LIMIT 1
                    """, (datetime.now(), sub['user_id']))
                
                sent_count += 1
            else:
                print(f"❌ Failed to send to {email}: {error}")
                failed_count += 1
        else:
            # Simulate sending
            print(f"📧 [SIMULATED] Would send {len(county_leads)} leads to {email} ({county_display})")
            sent_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Email Delivery Summary")
    print(f"{'='*60}")
    print(f"✅ Sent: {sent_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📧 Total: {len(subscriptions)}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    send_daily_leads()
