# 🚀 Production Deployment Checklist

Use this checklist to deploy your Contractor Leads SaaS to production.

## ✅ Pre-Deployment Checklist

### 1. Environment Setup

- [ ] Generate SECRET_KEY
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
  **Generated**: `3f9634751fa4b34565c48c3e9eeac16752a8ceffa7be01d0a85c9ddfe2610236`

- [ ] Get SendGrid API Key
  1. Sign up at [sendgrid.com](https://sendgrid.com)
  2. Verify sender email address
  3. Create API key with "Mail Send" permission
  4. Copy key (starts with `SG.`)

- [ ] Get Stripe Webhook Secret
  - **Development**: Use Stripe CLI
    ```bash
    brew install stripe/stripe-cli/stripe
    stripe login
    stripe listen --forward-to localhost:5003/stripe/webhook
    ```
  - **Production**: Add webhook in Stripe Dashboard → Developers → Webhooks

- [ ] Create `.env` file
  ```bash
  cp .env.template .env
  nano .env  # Fill in your values
  ```

### 2. Stripe Configuration

- [ ] Add metadata to Nashville payment link
  - state_key: `tennessee`
  - county_key: `nashville`

- [ ] Add metadata to Chattanooga payment link
  - state_key: `tennessee`
  - county_key: `chattanooga`

- [ ] Add metadata to Austin payment link
  - state_key: `texas`
  - county_key: `travis`

- [ ] Add metadata to San Antonio payment link
  - state_key: `texas`
  - county_key: `bexar`

📖 See `stripe_metadata_config.md` for detailed instructions

### 3. Dependencies

- [ ] Install Python packages
  ```bash
  pip3 install -r requirements.txt
  ```

- [ ] Test SendGrid
  ```bash
  python3 -c "import sendgrid; print('✅ SendGrid installed')"
  ```

### 4. Database

- [ ] Initialize database
  ```bash
  python3 database.py
  ```

- [ ] Verify test user exists
  ```bash
  sqlite3 contractor_leads.db "SELECT email FROM users WHERE email='test@example.com';"
  ```

### 5. Testing

- [ ] Run backend tests
  ```bash
  ./test_backend.sh
  ```

- [ ] Test email delivery (simulation)
  ```bash
  python3 email_sender.py
  ```

- [ ] Test Stripe webhooks locally
  ```bash
  stripe listen --forward-to localhost:5003/stripe/webhook
  # In another terminal:
  python3 app_backend.py
  # Make a test payment
  ```

## 🌐 Deployment

### Option 1: Local/Development Server

```bash
# Start in development mode
python3 app_backend.py

# Or start in production mode
./start_production.sh
```

### Option 2: Production Server (Linux)

```bash
# Run deployment script
./deploy.sh

# Start service
sudo systemctl start contractor-leads

# Enable on boot
sudo systemctl enable contractor-leads

# Check status
sudo systemctl status contractor-leads
```

### Option 3: Manual Production Start

```bash
# Start with gunicorn
gunicorn -w 4 -b 0.0.0.0:5003 --timeout 120 app_backend:app

# Or run in background
nohup gunicorn -w 4 -b 0.0.0.0:5003 --timeout 120 app_backend:app &
```

## ⏰ Cron Jobs Setup

- [ ] Set up daily scraping (1 AM)
- [ ] Set up daily emails (6 AM)

### Automatic Setup:
```bash
./setup_cron.sh
```

### Manual Setup:
```bash
crontab -e
```

Add these lines:
```cron
# Contractor Leads - Daily Scraping at 1:00 AM
0 1 * * * cd /Users/briceleasure/Desktop/contractor-leads-saas && /usr/bin/python3 incremental_scraper.py >> /Users/briceleasure/Desktop/contractor-leads-saas/logs/scraper.log 2>&1

# Contractor Leads - Daily Emails at 6:00 AM
0 6 * * * cd /Users/briceleasure/Desktop/contractor-leads-saas && /usr/bin/python3 email_sender.py >> /Users/briceleasure/Desktop/contractor-leads-saas/logs/email.log 2>&1
```

Verify:
```bash
crontab -l
```

## 🔒 Security

- [ ] Change SECRET_KEY from default
- [ ] Set STRIPE_WEBHOOK_SECRET
- [ ] Use HTTPS in production (required for Stripe)
- [ ] Restrict database file permissions
  ```bash
  chmod 600 contractor_leads.db
  ```
- [ ] Consider upgrading to bcrypt for passwords (optional)
- [ ] Set up database backups

## 📊 Monitoring

### Check Application Status
```bash
# Check if running
lsof -ti:5003

# Check logs (if using systemd)
sudo journalctl -u contractor-leads -f

# Check gunicorn logs
tail -f gunicorn.log
```

### Check Cron Jobs
```bash
# Scraper logs
tail -f logs/scraper.log

# Email logs
tail -f logs/email.log
```

### Database Queries
```bash
# Total users
sqlite3 contractor_leads.db "SELECT COUNT(*) FROM users;"

# Active subscriptions
sqlite3 contractor_leads.db "SELECT COUNT(*) FROM subscriptions WHERE status='active';"

# Revenue (assuming $49.99/month)
sqlite3 contractor_leads.db "SELECT COUNT(*) * 49.99 FROM subscriptions WHERE status='active';"
```

## ✅ Post-Deployment Verification

- [ ] Visit homepage: http://localhost:5003
- [ ] Test signup: Create new account
- [ ] Test login with test account
- [ ] View dashboard
- [ ] Check county page (should be protected)
- [ ] Create test subscription (via admin panel)
- [ ] View county page again (should show full addresses)
- [ ] Test email delivery
- [ ] Make test Stripe payment
- [ ] Verify webhook creates subscription
- [ ] Check user receives email

## 🆘 Troubleshooting

### App won't start
```bash
# Check for port conflicts
lsof -ti:5003

# Check Python version
python3 --version

# Check dependencies
pip3 list | grep -E "Flask|sendgrid|gunicorn"
```

### Webhooks not working
- Verify metadata is set correctly in Stripe
- Check webhook secret is set: `echo $STRIPE_WEBHOOK_SECRET`
- Test with Stripe CLI: `stripe listen --forward-to localhost:5003/stripe/webhook`
- Check Flask logs for errors

### Emails not sending
- Verify SendGrid API key: `echo $SENDGRID_API_KEY`
- Check sender email is verified in SendGrid
- Run test: `python3 email_sender.py`
- Check SendGrid dashboard for errors

### Database errors
```bash
# Check database exists
ls -lh contractor_leads.db

# Verify tables
sqlite3 contractor_leads.db ".tables"

# Reinitialize if needed
python3 database.py
```

## 📞 Support

- **Stripe Docs**: https://stripe.com/docs/webhooks
- **SendGrid Docs**: https://docs.sendgrid.com/
- **Flask Docs**: https://flask.palletsprojects.com/

---

## Quick Start Commands

```bash
# 1. Set up environment
cp .env.template .env
nano .env  # Fill in values

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Initialize database
python3 database.py

# 4. Test everything
./test_backend.sh

# 5. Start the app
python3 app_backend.py
# OR for production:
./start_production.sh

# 6. Set up cron jobs
./setup_cron.sh

# 7. Access the app
open http://localhost:5003
```

You're ready to launch! 🚀
