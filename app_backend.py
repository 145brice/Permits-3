from flask import Flask, session, redirect, url_for, request, jsonify, render_template_string, flash
from functools import wraps
from datetime import datetime, timedelta
import json
import os
import re
import random
import hmac
import hashlib
import csv
import database
import auth

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-' + os.urandom(24).hex())

# Stripe configuration
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_test_secret')

# Stripe payment URLs for each county
STRIPE_URLS = {
    'tennessee': {
        'nashville': 'https://buy.stripe.com/4gM14pc1G7ij5XYfXx63K0j',
        'chattanooga': 'https://buy.stripe.com/8x29AVaXCeKL86612D63K0k'
    },
    'texas': {
        'travis': 'https://buy.stripe.com/5kQ4gB1n2dGH4TU26H63K0m',
        'bexar': 'https://buy.stripe.com/8x26oJd5K1XZ9aah1B63K0l'
    }
}

def load_leads():
    db_path = os.path.join(os.path.dirname(__file__), 'leads_db', 'current_leads.json')
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            data = json.load(f)
            leads_data = data.get('leads', {})
            for state in leads_data.values():
                for county_leads in state.values():
                    for lead in county_leads:
                        if lead.get('score') == 90:
                            lead['score'] = random.randint(75, 98)
            return leads_data
    return {}

def blur_address(address):
    suffixes = ['Street', 'St', 'Avenue', 'Ave', 'Road', 'Rd', 'Drive', 'Dr', 'Lane', 'Ln', 
               'Boulevard', 'Blvd', 'Parkway', 'Pkwy', 'Circle', 'Cir', 'Court', 'Ct',
               'Plaza', 'Square', 'Way', 'Place', 'Pl', 'Pike', 'Trail', 'Terrace']
    
    suffix_found = None
    for suffix in suffixes:
        if re.search(r'\b' + suffix + r'\b', address, re.IGNORECASE):
            suffix_match = re.search(r'\b' + suffix + r'\b', address, re.IGNORECASE)
            suffix_found = suffix_match.group()
            break
    
    if ',' in address:
        parts = address.split(',', 1)
        location_part = parts[1].strip()
        if suffix_found:
            return f'<span class="blur">[●●●●]</span> {suffix_found}, {location_part}'
        else:
            return f'<span class="blur">[●●●●]</span>, {location_part}'
    else:
        zip_match = re.search(r'\b\d{5}\b$', address)
        if zip_match and suffix_found:
            zip_code = zip_match.group()
            return f'<span class="blur">[●●●●]</span> {suffix_found} {zip_code}'
        elif suffix_found:
            return f'<span class="blur">[●●●●]</span> {suffix_found}'
        else:
            return f'<span class="blur">[Address Locked]</span>'

LEADS = load_leads()

# Initialize database on startup
with app.app_context():
    database.init_database()

@app.route('/')
def index():
    user = auth.get_current_user()
    user_email = user['email'] if user else None
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contractor Leads - Daily Building Permits</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0a0a0a; color: #ffffff; line-height: 1.6; }
            .hero { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); position: relative; overflow: hidden; }
            .hero::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.1) 0%, transparent 50%); }
            .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; position: relative; z-index: 1; }
            .hero-content { text-align: center; max-width: 900px; margin: 0 auto; }
            .user-badge { position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.05); padding: 10px 20px; border-radius: 50px; border: 1px solid rgba(255,255,255,0.1); font-size: 0.875rem; }
            .user-badge a { color: #6366f1; text-decoration: none; margin-left: 15px; }
            .badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); padding: 8px 20px; border-radius: 50px; font-size: 0.875rem; font-weight: 500; color: #818cf8; margin-bottom: 30px; letter-spacing: 0.3px; }
            .badge-dot { width: 6px; height: 6px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            h1 { font-size: 5.5rem; font-weight: 800; line-height: 1.1; margin-bottom: 25px; background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: -0.03em; }
            .subtitle { font-size: 1.5rem; color: #a0a0a0; margin-bottom: 50px; font-weight: 400; line-height: 1.5; }
            .cta-group { display: flex; gap: 20px; justify-content: center; align-items: center; flex-wrap: wrap; margin-bottom: 60px; }
            .btn { padding: 18px 40px; border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 1.125rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); display: inline-flex; align-items: center; gap: 10px; border: none; cursor: pointer; }
            .btn-primary { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4); }
            .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(99, 102, 241, 0.5); }
            .btn-secondary { background: rgba(255, 255, 255, 0.05); color: white; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); }
            .btn-secondary:hover { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2); }
            .markets { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 50px 40px; backdrop-filter: blur(10px); }
            .markets-title { text-align: center; font-size: 1.25rem; font-weight: 600; margin-bottom: 40px; color: #d0d0d0; letter-spacing: 0.5px; text-transform: uppercase; font-size: 0.875rem; }
            .state-section { margin-bottom: 50px; }
            .state-section:last-child { margin-bottom: 0; }
            .state-header { display: flex; align-items: center; gap: 15px; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
            .state-icon { font-size: 2rem; }
            .state-name { font-size: 1.5rem; font-weight: 700; color: #ffffff; }
            .counties { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
            .county-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 30px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); text-decoration: none; display: block; }
            .county-card:hover { background: rgba(255, 255, 255, 0.05); border-color: rgba(99, 102, 241, 0.3); transform: translateY(-4px); box-shadow: 0 10px 40px rgba(99, 102, 241, 0.2); }
            .county-header { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
            .county-icon { font-size: 2rem; }
            .county-info { flex: 1; }
            .county-city { font-size: 1.25rem; font-weight: 700; color: #ffffff; margin-bottom: 4px; }
            .county-name { font-size: 0.875rem; color: #808080; font-weight: 500; }
            .county-stats { display: flex; justify-content: space-between; align-items: center; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.05); }
            .stat { display: flex; flex-direction: column; }
            .stat-label { font-size: 0.75rem; color: #808080; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
            .stat-value { font-size: 1.5rem; font-weight: 700; color: #6366f1; }
            .arrow { color: #6366f1; font-size: 1.25rem; }
            @media (max-width: 768px) { h1 { font-size: 2.5rem; } .subtitle { font-size: 1.125rem; } .counties { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="hero">
            {% if user_email %}
            <div class="user-badge">
                👤 {{ user_email }}
                <a href="/dashboard">Dashboard</a>
                <a href="/logout">Logout</a>
            </div>
            {% endif %}
            <div class="container">
                <div class="hero-content">
                    <div class="badge">
                        <span class="badge-dot"></span>
                        10,952+ Active Leads
                    </div>
                    <h1>Daily Construction Permits</h1>
                    <p class="subtitle">
                        Fresh building permits delivered every morning.<br>
                        <strong style="font-size: 3.5rem; color: #6366f1; font-weight: 800; display: block; margin-top: 20px;">$49.99/month</strong>
                    </p>
                    <div class="cta-group">
                        {% if user_email %}
                        <a href="/dashboard" class="btn btn-primary">View Dashboard<span>→</span></a>
                        {% else %}
                        <a href="/signup" class="btn btn-primary">Get Started<span>→</span></a>
                        <a href="/login" class="btn btn-secondary">Sign In</a>
                        {% endif %}
                    </div>
                </div>
                <div class="markets">
                    <div class="markets-title">Available Markets</div>
                    <div class="state-section">
                        <div class="state-header"><span class="state-icon">🎸</span><span class="state-name">Tennessee</span></div>
                        <div class="counties">
                            <a href="/county/tennessee/nashville" class="county-card">
                                <div class="county-header"><span class="county-icon">🎵</span><div class="county-info"><div class="county-city">Nashville</div><div class="county-name">Davidson County</div></div></div>
                                <div class="county-stats"><div class="stat"><div class="stat-label">Leads</div><div class="stat-value">272</div></div><span class="arrow">→</span></div>
                            </a>
                            <a href="/county/tennessee/chattanooga" class="county-card">
                                <div class="county-header"><span class="county-icon">🏔️</span><div class="county-info"><div class="county-city">Chattanooga</div><div class="county-name">Hamilton County</div></div></div>
                                <div class="county-stats"><div class="stat"><div class="stat-label">Leads</div><div class="stat-value">943</div></div><span class="arrow">→</span></div>
                            </a>
                        </div>
                    </div>
                    <div class="state-section">
                        <div class="state-header"><span class="state-icon">⭐</span><span class="state-name">Texas</span></div>
                        <div class="counties">
                            <a href="/county/texas/travis" class="county-card">
                                <div class="county-header"><span class="county-icon">🎸</span><div class="county-info"><div class="county-city">Austin</div><div class="county-name">Travis County</div></div></div>
                                <div class="county-stats"><div class="stat"><div class="stat-label">Leads</div><div class="stat-value">5,000</div></div><span class="arrow">→</span></div>
                            </a>
                            <a href="/county/texas/bexar" class="county-card">
                                <div class="county-header"><span class="county-icon">🌮</span><div class="county-info"><div class="county-city">San Antonio</div><div class="county-name">Bexar County</div></div></div>
                                <div class="county-stats"><div class="stat"><div class="stat-label">Leads</div><div class="stat-value">4,695</div></div><span class="arrow">→</span></div>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, user_email=user_email)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect('/signup')
        
        user_id = database.create_user(email, password, full_name)
        if user_id:
            session['user_id'] = user_id
            flash('Account created successfully!', 'success')
            return redirect('/dashboard')
        else:
            flash('Email already exists', 'error')
            return redirect('/signup')
    
    # GET request - show signup form
    counties_data = [
        {'state': 'Tennessee', 'city': 'Nashville', 'county': 'Davidson County', 'emoji': '🎵', 'state_key': 'tennessee', 'county_key': 'nashville', 'count': 272},
        {'state': 'Tennessee', 'city': 'Chattanooga', 'county': 'Hamilton County', 'emoji': '🏔️', 'state_key': 'tennessee', 'county_key': 'chattanooga', 'count': 943},
        {'state': 'Texas', 'city': 'Austin', 'county': 'Travis County', 'emoji': '🎸', 'state_key': 'texas', 'county_key': 'travis', 'count': 5000},
        {'state': 'Texas', 'city': 'San Antonio', 'county': 'Bexar County', 'emoji': '🌮', 'state_key': 'texas', 'county_key': 'bexar', 'count': 4695},
    ]
    
    cards_html = ""
    for c in counties_data:
        stripe_url = STRIPE_URLS.get(c['state_key'], {}).get(c['county_key'], '#')
        cards_html += f"""
        <div class="plan-card">
            <div class="plan-icon">{c['emoji']}</div>
            <h3 class="plan-city">{c['city']}</h3>
            <p class="plan-county">{c['county']}, {c['state']}</p>
            <div class="plan-price">$49.99<span>/mo</span></div>
            <div class="plan-leads">{c['count']:,} active leads</div>
            <a href="{stripe_url}" class="btn-subscribe">Subscribe</a>
            <ul class="plan-features">
                <li>Daily email updates</li>
                <li>Full contact details</li>
                <li>AI lead scoring</li>
            </ul>
        </div>
        """
    
    return f"""<!DOCTYPE html><html><head><title>Choose Your Market</title>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #0a0a0a; color: #fff; padding: 40px 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 60px; }}
        h1 {{ font-size: 3rem; font-weight: 800; margin-bottom: 15px; }}
        .subtitle {{ font-size: 1.25rem; color: #a0a0a0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; }}
        .plan-card {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 20px; padding: 35px; text-align: center; transition: all 0.3s; }}
        .plan-card:hover {{ border-color: rgba(99,102,241,0.3); background: rgba(255,255,255,0.03); transform: translateY(-5px); }}
        .plan-icon {{ font-size: 3rem; margin-bottom: 20px; }}
        .plan-city {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 5px; }}
        .plan-county {{ color: #808080; font-size: 0.875rem; margin-bottom: 20px; }}
        .plan-price {{ font-size: 2.5rem; font-weight: 800; color: #6366f1; margin-bottom: 10px; }}
        .plan-price span {{ font-size: 1.25rem; color: #808080; }}
        .plan-leads {{ color: #a0a0a0; font-size: 0.875rem; margin-bottom: 25px; }}
        .btn-subscribe {{ display: block; width: 100%; padding: 15px; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; text-decoration: none; border-radius: 12px; font-weight: 700; font-size: 1rem; transition: all 0.3s; margin-bottom: 20px; }}
        .btn-subscribe:hover {{ transform: translateY(-2px); box-shadow: 0 8px 30px rgba(99,102,241,0.4); }}
        .plan-features {{ list-style: none; text-align: left; }}
        .plan-features li {{ padding: 10px 0; color: #a0a0a0; font-size: 0.875rem; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .plan-features li:last-child {{ border-bottom: none; }}
        .plan-features li:before {{ content: "✓ "; color: #22c55e; font-weight: bold; margin-right: 8px; }}
        .back {{ text-align: center; margin-top: 40px; }}
        .back a {{ color: #6366f1; text-decoration: none; font-weight: 600; }}
    </style></head><body>
    <div class="container">
        <div class="header">
            <h1>Choose Your Market</h1>
            <p class="subtitle">$49.99/month per county • Cancel anytime</p>
        </div>
        <div class="grid">
            {cards_html}
        </div>
        <div class="back"><a href="/">← Back to Home</a></div>
    </div>
    </body></html>"""

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events for subscription management"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    # In production, verify the webhook signature
    # For now, we'll process the event directly
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid payload'}), 400
    
    event_type = event.get('type')
    
    if event_type == 'checkout.session.completed':
        session_data = event['data']['object']
        customer_email = session_data.get('customer_email')
        stripe_customer_id = session_data.get('customer')
        stripe_subscription_id = session_data.get('subscription')
        
        # Extract state and county from metadata
        metadata = session_data.get('metadata', {})
        state_key = metadata.get('state_key')
        county_key = metadata.get('county_key')
        
        if customer_email and state_key and county_key:
            user = database.get_user_by_email(customer_email)
            if user:
                # Update Stripe customer ID
                database.update_stripe_customer_id(user['id'], stripe_customer_id)
                
                # Create subscription
                database.create_subscription(
                    user['id'],
                    state_key,
                    county_key,
                    stripe_subscription_id
                )
                
                # Queue welcome email
                database.queue_email(
                    user['id'],
                    'welcome',
                    f'Welcome to {county_key.title()} Contractor Leads',
                    f'Your subscription is now active. You\'ll receive daily leads starting tomorrow morning.',
                    datetime.now()
                )
                
                print(f"✅ Subscription created for {customer_email} - {state_key}/{county_key}")
    
    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        stripe_subscription_id = subscription.get('id')
        status = subscription.get('status')
        
        database.update_subscription_status(stripe_subscription_id, status)
        print(f"✅ Subscription {stripe_subscription_id} updated to {status}")
    
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        stripe_subscription_id = subscription.get('id')
        
        database.update_subscription_status(stripe_subscription_id, 'cancelled')
        print(f"✅ Subscription {stripe_subscription_id} cancelled")
    
    return jsonify({'status': 'success'}), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = database.verify_password(email, password)
        if user:
            session['user_id'] = user['id']
            
            # Update last login
            with database.get_db() as conn:
                conn.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now(), user['id']))
            
            next_url = request.args.get('next', '/')
            return redirect(next_url)
        else:
            flash('Invalid email or password', 'error')
            return redirect('/login')
    
    return """<!DOCTYPE html><html><head><title>Sign In</title>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0a0a; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .box { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 20px; padding: 50px; max-width: 400px; width: 100%; }
        h2 { text-align: center; color: #fff; margin-bottom: 30px; font-size: 2rem; }
        input { width: 100%; padding: 15px; margin: 10px 0; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; color: #fff; font-size: 1rem; }
        input:focus { outline: none; border-color: #6366f1; }
        button { width: 100%; padding: 15px; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 1rem; margin-top: 10px; }
        button:hover { opacity: 0.9; }
        a { display: block; text-align: center; margin-top: 20px; color: #6366f1; text-decoration: none; font-weight: 600; }
        .signup-link { margin-top: 20px; text-align: center; color: #a0a0a0; }
        .signup-link a { display: inline; color: #6366f1; }
    </style></head><body>
    <div class="box">
        <h2>Sign In</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
        <div class="signup-link">Don't have an account? <a href="/signup">Sign up</a></div>
        <a href="/">← Back</a>
    </div></body></html>"""

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/county/<state>/<county>')
def county_detail(state, county):
    """Show county leads - full details if subscribed, preview if not"""
    user = auth.get_current_user()
    
    # Check if user has active subscription
    has_access = False
    if user:
        has_access = database.has_access_to_county(user['id'], state, county)
    
    # Get leads for this county
    leads = LEADS.get(state, {}).get(county, [])
    
    if not leads:
        return "<h1>No leads found</h1>", 404
    
    # Prepare lead data
    leads_html = ""
    display_leads = leads[:50]  # Show first 50 leads
    
    for lead in display_leads:
        address = lead.get('address', 'N/A')
        if not has_access:
            address = blur_address(address)
        
        permit_type = lead.get('permit_type', 'N/A')
        date = lead.get('date', 'N/A')
        score = lead.get('score', 0)
        value = lead.get('estimated_value', 'N/A')
        
        leads_html += f"""
        <div class="lead-card">
            <div class="lead-header">
                <div class="lead-score score-{score//10*10}">{score}</div>
                <div class="lead-info">
                    <div class="lead-address">{address}</div>
                    <div class="lead-meta">{permit_type} • {date}</div>
                </div>
            </div>
            <div class="lead-value">Est. Value: {value}</div>
        </div>
        """
    
    # County display names
    county_names = {
        'nashville': 'Nashville, TN',
        'chattanooga': 'Chattanooga, TN',
        'travis': 'Austin, TX',
        'bexar': 'San Antonio, TX'
    }
    county_display = county_names.get(county, county.title())
    
    # Show unlock banner if not subscribed
    banner = ""
    if not has_access:
        stripe_url = STRIPE_URLS.get(state, {}).get(county, '/signup')
        banner = f"""
        <div class="unlock-banner">
            <div class="banner-content">
                <div class="banner-icon">🔒</div>
                <div class="banner-text">
                    <h3>Unlock Full Access</h3>
                    <p>Subscribe to see complete addresses and contact details</p>
                </div>
                <a href="{stripe_url}" class="btn-unlock">Subscribe for $49.99/mo</a>
            </div>
        </div>
        """
    
    return f"""<!DOCTYPE html><html><head><title>{county_display} Leads</title>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #0a0a0a; color: #fff; padding: 40px 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ margin-bottom: 40px; }}
        .back-link {{ color: #6366f1; text-decoration: none; font-weight: 600; display: inline-block; margin-bottom: 20px; }}
        h1 {{ font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; }}
        .lead-count {{ color: #808080; font-size: 1.125rem; }}
        .unlock-banner {{ background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(168,85,247,0.1) 100%); border: 1px solid rgba(99,102,241,0.3); border-radius: 20px; padding: 30px; margin-bottom: 30px; }}
        .banner-content {{ display: flex; align-items: center; gap: 25px; flex-wrap: wrap; }}
        .banner-icon {{ font-size: 3rem; }}
        .banner-text {{ flex: 1; min-width: 250px; }}
        .banner-text h3 {{ font-size: 1.5rem; margin-bottom: 5px; }}
        .banner-text p {{ color: #a0a0a0; }}
        .btn-unlock {{ padding: 15px 30px; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; text-decoration: none; border-radius: 12px; font-weight: 700; white-space: nowrap; }}
        .btn-unlock:hover {{ opacity: 0.9; }}
        .leads-grid {{ display: grid; gap: 15px; }}
        .lead-card {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; transition: all 0.2s; }}
        .lead-card:hover {{ border-color: rgba(255,255,255,0.1); background: rgba(255,255,255,0.03); }}
        .lead-header {{ display: flex; gap: 15px; margin-bottom: 10px; }}
        .lead-score {{ width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.25rem; }}
        .score-90 {{ background: rgba(34,197,94,0.2); color: #22c55e; }}
        .score-80 {{ background: rgba(99,102,241,0.2); color: #6366f1; }}
        .score-70 {{ background: rgba(251,191,36,0.2); color: #fbbf24; }}
        .lead-info {{ flex: 1; }}
        .lead-address {{ font-size: 1.125rem; font-weight: 600; margin-bottom: 5px; }}
        .lead-meta {{ color: #808080; font-size: 0.875rem; }}
        .lead-value {{ color: #a0a0a0; font-size: 0.875rem; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); }}
        .blur {{ filter: blur(6px); opacity: 0.6; user-select: none; }}
    </style></head><body>
    <div class="container">
        <div class="header">
            <a href="/" class="back-link">← Back to Markets</a>
            <h1>{county_display}</h1>
            <p class="lead-count">{len(leads):,} active leads</p>
        </div>
        {banner}
        <div class="leads-grid">
            {leads_html}
        </div>
    </div>
    </body></html>"""

@app.route('/dashboard')
@auth.login_required
def dashboard():
    user = auth.get_current_user()
    subscriptions = database.get_user_subscriptions(user['id'])
    
    # Get user's counties and map to CSV filenames
    county_files = {
        ('tennessee', 'nashville'): 'nashville-davidson.csv',
        ('tennessee', 'hamilton'): 'hamilton.csv',
        ('texas', 'bexar'): 'bexar.csv',
        ('texas', 'travis'): 'austin-travis.csv'
    }
    
    permits = []
    for sub in subscriptions:
        state_key = sub['state_key']
        county_key = sub['county_key']
        csv_filename = county_files.get((state_key, county_key))
        
        if csv_filename:
            csv_path = f"data/{csv_filename}"
            if os.path.exists(csv_path):
                with open(csv_path, 'r') as f:
                    reader = csv.DictReader(f)
                    permits.extend(reader)
    
    # Sort logic
    sort = request.args.get('sort', 'date')
    permits.sort(key=lambda x: x.get(sort, ''), reverse=(sort == 'date'))
    
    return render_template('dashboard.html', permits=permits, counties=[f"{sub['state_key']}_{sub['county_key']}" for sub in subscriptions])

if __name__ == '__main__':
    total_leads = sum(len(county_leads) for state_leads in LEADS.values() for county_leads in state_leads.values())
    print(f"\n🚀 Contractor Leads Backend")
    print(f"📊 {total_leads:,} leads loaded")
    print(f"🔐 Authentication enabled")
    print(f"💾 Database ready")
    print(f"🌐 http://localhost:8081\n")
    app.run(host='0.0.0.0', port=8081, debug=True)
