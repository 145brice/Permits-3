"""
Flask web application - Dashboard and API
# Force redeploy trigger - 2025-11-23
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_cors import CORS
import argparse
from functools import wraps
from datetime import datetime
import os

import csv
from pathlib import Path
import io

from firebase_backend import FirebaseBackend
from stripe_payment import StripePayment
from email_service import EmailService
import config
from auth import login_required

print("DEBUG: app.py module loaded")

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
CORS(app)

@app.before_request
def before_request():
    print(f"DEBUG: REQUEST RECEIVED - {request.method} {request.path}")

# Add custom Jinja2 filters
@app.template_filter('number_format')
def number_format(value):
    """Format a number with commas and no decimal places"""
    try:
        return f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return value

firebase = None  # FirebaseBackend()  # Disabled to prevent crashes
stripe_payment = StripePayment()
email_service = EmailService()


# ==================== Routes ====================

@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user, stripe_publishable_key=config.STRIPE_PUBLISHABLE_KEY)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if firebase:
            user = firebase.create_user(email, password)
            if user and 'error' not in user:
                session['user_id'] = user['uid']
                session['email'] = user['email']
                return redirect(url_for('index'))
            else:
                error_msg = user.get('error', 'Failed to create account') if user else 'Failed to create account'
                return render_template('signup.html', error=error_msg)
        else:
            # Mock signup
            session['user_id'] = 'mock_' + email.replace('@', '_')
            session['email'] = email
            return redirect(url_for('index'))
    
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
@login_required
def subscribe():
    """Subscription page - redirect to main page for now"""
    # TODO: Implement proper subscription flow with Stripe
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - shows daily leads"""
    user_id = session.get('user_id')
    user = firebase.get_user(user_id) if firebase else {'email': session.get('email', 'demo@example.com')}
    
    # Get today's leads
    date_str = datetime.now().strftime('%Y-%m-%d')
    leads = firebase.get_daily_leads(date_str) if firebase else [
        {
            "county": "Nashville-Davidson",
            "permit_number": "DEMO-001",
            "address": "123 Main St, Nashville, TN",
            "permit_type": "Residential Addition",
            "estimated_value": 50000,
            "work_description": "Kitchen remodel and addition",
            "date": date_str
        }
    ]
    
    return render_template('dashboard.html', 
                          user=user,
                          leads=leads,
                          date=date_str)


@app.route('/archives')
@login_required
def archives():
    """Archives page - shows historical CSV files"""
    user_id = session.get('user_id')
    user = firebase.get_user(user_id) if firebase else {'email': session.get('email', 'demo@example.com')}
    
    # Get user's subscriptions
    subscriptions = firebase.get_user_subscriptions(user_id) if firebase and hasattr(firebase, 'get_user_subscriptions') else [{'county': 'Nashville-Davidson'}, {'county': 'Bexar'}]
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
@login_required
def view_csv(filename):
    """View CSV file as sortable table"""
    user_id = session.get('user_id')
    user = firebase.get_user(user_id) if firebase else {'email': session.get('email', 'demo@example.com')}
    
    # Get user's subscriptions
    subscriptions = firebase.get_user_subscriptions(user_id) if firebase and hasattr(firebase, 'get_user_subscriptions') else [{'county': 'Nashville-Davidson'}, {'county': 'Bexar'}]
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
@login_required
def download_pdf(date):
    """Download PDF report for specific date"""
    leads = firebase.get_daily_leads(date) if firebase else [
        {
            "county": "Nashville-Davidson",
            "permit_number": "DEMO-001",
            "address": "123 Main St, Nashville, TN",
            "permit_type": "Residential Addition",
            "estimated_value": 50000,
            "work_description": "Kitchen remodel and addition",
            "date": date
        }
    ]
    
    if not leads:
        return "No leads for this date", 404
    
    pdf_buffer = email_service.generate_leads_pdf(leads, date)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'contractor_leads_{date}.pdf'
    )


@app.route('/download_all_permits')
@login_required
def download_all_permits():
    """Download all permits as CSV"""
    import csv
    from io import StringIO
    
    # Pull master list from scraped_permits directory (same logic as admin route)
    master = []
    data_dir = Path('scraped_permits')
    if data_dir.exists():
        for csv_file in data_dir.glob('*.csv'):
            city_name = csv_file.name.split('_')[0]  # Extract city from filename
            # Map city names to slugs
            city_map = {
                'sanantonio': 'bexar',
                'nashville': 'davidson',
                'austin': 'travis',
                'hamilton': 'hamilton'
            }
            city_slug = city_map.get(city_name, city_name)
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row['city'] = city_slug
                        # Add pull_time if not present (use file modification time)
                        if 'pull_time' not in row:
                            row['pull_time'] = datetime.fromtimestamp(csv_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        master.append(row)
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
    
    # Also load from data/permits.csv if it exists (for mock data)
    permits_file = Path('data/permits.csv')
    if permits_file.exists():
        try:
            with open(permits_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Map county to city slug for consistency
                    county = row.get('county', '')
                    city_map = {
                        'Nashville-Davidson': 'davidson',
                        'Bexar': 'bexar', 
                        'Hamilton': 'hamilton',
                        'Austin-Travis': 'travis'
                    }
                    row['city'] = city_map.get(county, county.lower().replace(' ', '_'))
                    # Add pull_time if not present
                    if 'pull_time' not in row:
                        row['pull_time'] = row.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    master.append(row)
        except Exception as e:
            print(f"Error reading permits.csv: {e}")
    
    # Sort by pull_time (most recent first)
    master.sort(key=lambda x: x.get('pull_time', ''), reverse=True)
    
    if not master:
        return "No permits available", 404
    
    # Create CSV in memory
    output = StringIO()
    if master:
        fieldnames = master[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(master)
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'all_permits_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@app.route('/download_permit/<permit_number>')
@login_required
def download_permit(permit_number):
    """Download individual permit as CSV"""
    import csv
    from io import StringIO
    
    # Pull master list from scraped_permits directory (same logic as admin route)
    master = []
    data_dir = Path('scraped_permits')
    if data_dir.exists():
        for csv_file in data_dir.glob('*.csv'):
            city_name = csv_file.name.split('_')[0]  # Extract city from filename
            # Map city names to slugs
            city_map = {
                'sanantonio': 'bexar',
                'nashville': 'davidson',
                'austin': 'travis',
                'hamilton': 'hamilton'
            }
            city_slug = city_map.get(city_name, city_name)
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row['city'] = city_slug
                        # Add pull_time if not present (use file modification time)
                        if 'pull_time' not in row:
                            row['pull_time'] = datetime.fromtimestamp(csv_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        master.append(row)
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
    
    # Also load from data/permits.csv if it exists (for mock data)
    permits_file = Path('data/permits.csv')
    if permits_file.exists():
        try:
            with open(permits_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Map county to city slug for consistency
                    county = row.get('county', '')
                    city_map = {
                        'Nashville-Davidson': 'davidson',
                        'Bexar': 'bexar', 
                        'Hamilton': 'hamilton',
                        'Austin-Travis': 'travis'
                    }
                    row['city'] = city_map.get(county, county.lower().replace(' ', '_'))
                    # Add pull_time if not present
                    if 'pull_time' not in row:
                        row['pull_time'] = row.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    master.append(row)
        except Exception as e:
            print(f"Error reading permits.csv: {e}")
    
    # Find the specific permit
    permit = None
    for p in master:
        if p.get('permit_number') == permit_number:
            permit = p
            break
    
    if not permit:
        return "Permit not found", 404
    
    # Create CSV with just this permit
    output = StringIO()
    fieldnames = permit.keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(permit)
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'permit_{permit_number}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
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
        if firebase:
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
@app.route('/library')
@login_required
def library():
    """Library page - shows all permits and user's subscribed permits"""
    user_id = session.get('user_id')
    user = firebase.get_user(user_id) if firebase else {'email': session.get('email', 'demo@example.com')}
    
    # Get user's subscriptions to determine which counties they have access to
    subscriptions = firebase.get_user_subscriptions(user_id) if firebase and hasattr(firebase, 'get_user_subscriptions') else [{'county': 'Nashville-Davidson'}, {'county': 'Bexar'}]
    user_counties = [sub.get('county', '').lower().replace(' ', '_') for sub in subscriptions]
    
    # 1. Pull master list from scraped_permits directory
    master = []
    data_dir = Path('scraped_permits')
    if data_dir.exists():
        for csv_file in data_dir.glob('*.csv'):
            city_name = csv_file.name.split('_')[0]  # Extract city from filename
            # Map city names to slugs
            city_map = {
                'sanantonio': 'bexar',
                'nashville': 'davidson',
                'austin': 'travis',
                'hamilton': 'hamilton'
            }
            city_slug = city_map.get(city_name, city_name)
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row['city'] = city_slug
                        # Add pull_time if not present (use file modification time)
                        if 'pull_time' not in row:
                            row['pull_time'] = datetime.fromtimestamp(csv_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        master.append(row)
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
    
    # Also load from data/permits.csv if it exists (for mock data)
    permits_file = Path('data/permits.csv')
    if permits_file.exists():
        try:
            with open(permits_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Map county to city slug
                    county = row.get('county', '')
                    city_map = {
                        'Nashville-Davidson': 'davidson',
                        'Bexar': 'bexar', 
                        'Hamilton': 'hamilton',
                        'Austin-Travis': 'travis'
                    }
                    row['city'] = city_map.get(county, county.lower().replace(' ', '_'))
                    # Add pull_time if not present
                    if 'pull_time' not in row:
                        row['pull_time'] = row.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    master.append(row)
        except Exception as e:
            print(f"Error reading permits.csv: {e}")
    
    # 2. Pull only what they bought (filter by subscribed counties)
    user_permits = [p for p in master if p.get('city', '').lower() in user_counties]
    
    # Sort both by pull_time (most recent first)
    master.sort(key=lambda x: x.get('pull_time', ''), reverse=True)
    user_permits.sort(key=lambda x: x.get('pull_time', ''), reverse=True)
    
    return render_template('library.html', master=master, user_permits=user_permits, user=user)
@app.route('/admin')
@login_required
def admin():
    """Admin page - shows all permits with filtering and sorting"""
    user_id = session.get('user_id')
    
    # Simple admin check - check if user_id is in admin list
    # For now, allow any logged-in user (remove Firebase dependency)
    if not user_id:
        return redirect(url_for('index'))
    
    # For demo purposes, allow all logged-in users to access admin
    # In production, you'd check user roles/permissions
    
    user = {'email': session.get('email', 'unknown@example.com')}  # Mock user object
    
    # Pull master list from scraped_permits directory
    master = []
    data_dir = Path('scraped_permits')
    if data_dir.exists():
        for csv_file in data_dir.glob('*.csv'):
            city_name = csv_file.name.split('_')[0]  # Extract city from filename
            # Map city names to slugs
            city_map = {
                'sanantonio': 'bexar',
                'nashville': 'davidson',
                'austin': 'travis',
                'hamilton': 'hamilton'
            }
            city_slug = city_map.get(city_name, city_name)
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row['city'] = city_slug
                        # Add pull_time if not present (use file modification time)
                        if 'pull_time' not in row:
                            row['pull_time'] = datetime.fromtimestamp(csv_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        master.append(row)
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
    
    # Also load from data/permits.csv if it exists (for mock data)
    permits_file = Path('data/permits.csv')
    if permits_file.exists():
        try:
            with open(permits_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Map county to city slug for consistency
                    county = row.get('county', '')
                    city_map = {
                        'Nashville-Davidson': 'davidson',
                        'Bexar': 'bexar', 
                        'Hamilton': 'hamilton',
                        'Austin-Travis': 'travis'
                    }
                    row['city'] = city_map.get(county, county.lower().replace(' ', '_'))
                    # Add pull_time if not present
                    if 'pull_time' not in row:
                        row['pull_time'] = row.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    master.append(row)
        except Exception as e:
            print(f"Error reading permits.csv: {e}")
    
    # Sort by pull_time (most recent first)
    master.sort(key=lambda x: x.get('pull_time', ''), reverse=True)
    
    # Get unique cities for filtering
    cities = sorted(list(set(p.get('city', '') for p in master if p.get('city'))))
    
    # Calculate total value
    total_value = sum(int(p.get('estimated_value', 0) or 0) for p in master)
    
    return render_template('admin.html', master=master, cities=cities, user=user, total_value=total_value)
@app.route('/success')
def success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    if session_id:
        # Here you could verify the payment and activate the subscription
        return render_template('success.html')
    return redirect(url_for('index'))
def create_checkout():
    """Create Stripe checkout session"""
    try:
        data = request.get_json()
        city = data.get('city')
        email = data.get('email')
        
        if not city or not email:
            return jsonify({'error': 'Missing city or email'}), 400
        
        # Create checkout session
        success_url = request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = request.host_url
        
        session_data = stripe_payment.create_checkout_session(
            email, 
            f"user_{email.replace('@', '_')}",
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if not session_data:
            return jsonify({'error': 'Failed to create checkout session'}), 500
        
        return jsonify({'id': session_data['session_id']})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


print("DEBUG: API route registered")

@app.route('/create_checkout', methods=['POST'])
def create_checkout_route():
    return create_checkout()

@app.route('/api/test')
def api_test():
    return jsonify({'status': 'ok', 'message': 'API is working'})

@app.route('/api/permits/<int:year>/<int:month>/<int:day>')
def api_permits_date(year, month, day):
    date_str = f"{year}-{month:02d}-{day:02d}"
    leads = firebase.get_daily_leads(date_str) if firebase else [
        {
            "county": "Nashville-Davidson",
            "permit_number": "DEMO-001",
            "address": "123 Main St, Nashville, TN",
            "permit_type": "Residential Addition",
            "estimated_value": 50000,
            "work_description": "Kitchen remodel and addition",
            "date": date_str
        }
    ]
    return jsonify(leads)

if __name__ == '__main__':
    print(f"🚀 Starting Contractor Leads on http://localhost:8003")
    try:
        app.run(host='127.0.0.1', port=8003, debug=False, threaded=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        import traceback
        traceback.print_exc()
# Force redeploy trigger - Sun Nov 23 20:07:26 CST 2025
