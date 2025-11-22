"""
Flask web application - Dashboard and API
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_cors import CORS
import argparse
from functools import wraps
from datetime import datetime
import os

import csv
from pathlib import Path

from firebase_backend import FirebaseBackend
from stripe_payment import StripePayment
from email_service import EmailService
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
CORS(app)

# Add custom Jinja2 filters
@app.template_filter('number_format')
def number_format(value):
    """Format a number with commas and no decimal places"""
    try:
        return f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return value

firebase = FirebaseBackend()
stripe_payment = StripePayment()
email_service = EmailService()


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== Routes ====================

@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = firebase.create_user(email, password)
        if user and 'error' not in user:
            session['user_id'] = user['uid']
            session['email'] = user['email']
            return redirect(url_for('index'))
        else:
            error_msg = user.get('error', 'Failed to create account') if user else 'Failed to create account'
            return render_template('signup.html', error=error_msg)
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # For testing, accept any login
        session['user_id'] = 'test_user_' + email.replace('@', '_')
        session['email'] = email
        return redirect(url_for('index'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/subscribe')
# @login_required
def subscribe():
    """Subscription page - redirect to main page for now"""
    # TODO: Implement proper subscription flow with Stripe
    return redirect(url_for('index'))


@app.route('/dashboard')
# @login_required
def dashboard():
    """Main dashboard - shows daily leads"""
    user_id = session.get('user_id')
    user = firebase.get_user(user_id)
    
    # Get today's leads
    date_str = datetime.now().strftime('%Y-%m-%d')
    leads = firebase.get_daily_leads(date_str)
    
    return render_template('dashboard.html', 
                          user=user,
                          leads=leads,
                          date=date_str)


@app.route('/archives')
# @login_required
def archives():
    """Archives page - shows historical CSV files"""
    user_id = session.get('user_id')
    user = firebase.get_user(user_id)
    
    # Get user's subscriptions
    subscriptions = firebase.get_user_subscriptions(user_id) if user_id else []
    subscribed_counties = [sub.get('county', '') for sub in subscriptions]
    
    # Map county names to slugs
    county_map = {
        'Nashville-Davidson': 'davidson',
        'Bexar': 'bexar',
        'Hamilton': 'hamilton',
        'Travis': 'travis'
    }
    subscribed_slugs = [county_map.get(county, county.lower().replace(' ', '_')) for county in subscribed_counties]
    
    # Find CSV files for subscribed counties
    csv_files = {}
    data_dir = Path('data')
    if data_dir.exists():
        for slug in subscribed_slugs:
            pattern = f"{slug}_permits_*.csv"
            files = list(data_dir.glob(pattern))
            if files:
                # Sort by date descending
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                csv_files[slug] = [(f.name, f.stat().st_mtime) for f in files]
    
    return render_template('archives.html', csv_files=csv_files, county_map=county_map)


@app.route('/view_csv/<filename>')
# @login_required
def view_csv(filename):
    """View CSV file as sortable table"""
    user_id = session.get('user_id')
    user = firebase.get_user(user_id)
    
    # Get user's subscriptions
    subscriptions = firebase.get_user_subscriptions(user_id) if user_id else []
    subscribed_counties = [sub.get('county', '') for sub in subscriptions]
    
    # Map to slugs
    county_map = {
        'Nashville-Davidson': 'davidson',
        'Bexar': 'bexar',
        'Hamilton': 'hamilton',
        'Travis': 'travis'
    }
    subscribed_slugs = [county_map.get(county, county.lower().replace(' ', '_')) for county in subscribed_counties]
    
    # Check if file belongs to subscribed county
    file_path = Path('data') / filename
    if not file_path.exists():
        return "File not found", 404
    
    slug = filename.split('_')[0]
    if slug not in subscribed_slugs:
        return "Access denied", 403
    
    # Read CSV
    permits = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            permits = list(reader)
    except Exception as e:
        return f"Error reading file: {e}", 500
    
    return render_template('view_csv.html', permits=permits, filename=filename)


@app.route('/download_pdf/<date>')
# @login_required
def download_pdf(date):
    """Download PDF report for specific date"""
    leads = firebase.get_daily_leads(date)
    
    if not leads:
        return "No leads for this date", 404
    
    pdf_buffer = email_service.generate_leads_pdf(leads, date)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'contractor_leads_{date}.pdf'
    )


@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    event = stripe_payment.handle_webhook(payload, sig_header)
    
    if not event:
        return 'Invalid signature', 400
    
    event_type = event['type']
    event_data = event['data']
    
    # Handle different event types
    if event_type == 'checkout.session.completed':
        # Activate subscription
        user_id = event_data.get('user_id')
        firebase.update_user_subscription(
            user_id,
            event_data['customer_id'],
            event_data['subscription_id'],
            'active'
        )
    
    elif event_type == 'customer.subscription.deleted':
        # Deactivate subscription
        # Find user by customer_id and update
        pass
    
    return jsonify({'status': 'success'})
@app.route('/success')
# @login_required
def success():
    """Payment success page"""
    return render_template('success.html')
@app.route('/buy/<plan>')
def buy_plan(plan):
    """Redirect to Stripe payment link for specific plan"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Map plan names to Stripe payment links
    payment_links = {
        'Bexar': 'https://buy.stripe.com/4gM5kF0iY0TVgCC12D63K0n',
        'Davidson': 'https://buy.stripe.com/3cI00laXCauv722h1B63K0q',
        'Hamilton': 'https://buy.stripe.com/dRmeVf0iYgST2LM9z963K0p',
        'Austin-Travis': 'https://buy.stripe.com/8x25kF9TygST8663aL63K0o'
    }
    
    if plan in payment_links:
        return redirect(payment_links[plan])
    
    return "Plan not found", 404


def run():
    port = int(os.getenv('PORT', 8080))
    print(f"🚀 Starting Contractor Leads on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=(config.FLASK_ENV == 'development'))
if __name__ == '__main__':
    run()
