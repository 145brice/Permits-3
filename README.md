# Contractor Leads SaaS

**Daily building permit intelligence for contractors in Tennessee**

Automatically scrapes building permit applications from 5 Tennessee counties (Nashville-Davidson, Rutherford, Wilson, Sumner), scores them with AI, and delivers the top 10 leads via email every morning.

## 🚀 Features

- **5 County Coverage**: Nashville-Davidson, Rutherford, Wilson, Sumner
- **AI Lead Scoring**: HuggingFace model scores permits based on:
  - Job size (estimated value)
  - Location desirability
  - Project urgency
  - Permit type profitability
- **Daily Email Reports**: Top 10 leads with PDF attachment
- **Simple Dashboard**: View leads, download PDFs
- **Stripe Integration**: $20/month subscription
- **Firebase Backend**: User auth, data storage
- **Nightly Automation**: Scheduled scraping at 2 AM

## 📋 Requirements

- Python 3.9+
- Firebase account & credentials
- Stripe account (test/live keys)
- SMTP email account (Gmail recommended)

## ⚙️ Installation

### 1. Clone and Setup

```bash
cd /tmp/contractor-leads-saas
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```env
# Firebase
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...

# Email (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@contractorleads.com

# App
SECRET_KEY=your-random-secret-key-here
FLASK_ENV=development
```

### 3. Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Firestore Database
3. Enable Authentication (Email/Password)
4. Download service account credentials
5. Save as `firebase-credentials.json` in project root

### 4. Stripe Setup

1. Create Stripe account at https://stripe.com
2. Create a Product with $20/month recurring price
3. Copy the Price ID to `.env`
4. Set up webhook endpoint: `https://yourdomain.com/webhook/stripe`
5. Subscribe to events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

### 5. Email Setup (Gmail)

1. Enable 2-factor authentication on Gmail
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in `.env`

## 🏃 Running the Application

### Development Mode

```bash
# Terminal 1: Run Flask app
python app.py

# Terminal 2: Run scheduler (nightly jobs)
python scheduler.py
```

Visit: http://localhost:5000

### Production Deployment

#### Using Gunicorn

```bash
# Run Flask app
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Run scheduler in background
nohup python scheduler.py &
```

#### Using System Cron (Alternative to scheduler.py)

```bash
# Edit crontab
crontab -e

# Add nightly job at 2 AM
0 2 * * * cd /path/to/contractor-leads-saas && venv/bin/python -c "from scheduler import LeadScheduler; LeadScheduler().run_nightly_job()"
```

## 📁 Project Structure

```
contractor-leads-saas/
├── app.py                   # Flask web application
├── scheduler.py             # Nightly job scheduler
├── config.py                # Configuration loader
├── ai_scorer.py             # AI lead scoring
├── firebase_backend.py      # Firebase integration
├── stripe_payment.py        # Stripe payment handling
├── email_service.py         # Email & PDF generation
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py     # Base scraper class
│   ├── nashville_scraper.py
│   ├── rutherford_scraper.py
│   ├── wilson_scraper.py
│   ├── sumner_scraper.py
│   └── orchestrator.py     # Runs all scrapers
├── templates/
│   ├── index.html          # Landing page
│   ├── signup.html         # User signup
│   ├── login.html          # User login
│   └── dashboard.html      # Main dashboard
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Customization

### Adding New Counties

1. Create new scraper in `scrapers/` inheriting from `PermitScraper`
2. Implement `scrape()` method
3. Add to `ScraperOrchestrator` in `orchestrator.py`

### Adjusting AI Scoring

Edit `ai_scorer.py`:
- Modify score weights in `score_permit()`
- Add premium areas in `premium_areas` list
- Adjust value thresholds in `_score_job_size()`

### Changing Scrape Time

Edit `.env`:
```
SCRAPE_TIME=03:00  # 3 AM
```

## 🧪 Testing

### Test Scraper

```bash
python -c "from scrapers import ScraperOrchestrator; permits = ScraperOrchestrator().scrape_all(); print(f'Found {len(permits)} permits')"
```

### Test AI Scorer

```bash
python -c "from ai_scorer import LeadScorer; scorer = LeadScorer(); print('Model loaded successfully')"
```

### Test Email

```bash
python -c "from email_service import EmailService; EmailService().send_daily_leads('test@example.com', [], '2025-01-01')"
```

### Run Manual Job

```bash
python -c "from scheduler import LeadScheduler; LeadScheduler().run_nightly_job()"
```

## 🚨 Important Notes

### Website Scrapers

The scrapers in this project are **templates**. You must:

1. Inspect actual county websites
2. Update selectors/parsing logic to match real HTML/PDF structure
3. Handle authentication if required
4. Respect robots.txt and rate limits
5. Add error handling for site changes

### Legal Compliance

- Ensure you have permission to scrape these websites
- Public data is generally OK, but check terms of service
- Add User-Agent header (already included)
- Implement rate limiting if needed

### Production Considerations

- Use environment variables (never commit `.env`)
- Set up proper logging
- Implement monitoring/alerts
- Use production Firebase/Stripe accounts
- Enable HTTPS
- Add database backups
- Scale with Docker/Kubernetes if needed

## 📊 Monitoring

Check logs for:
- Scraping errors
- Scoring failures
- Email delivery issues
- Payment webhook events

```bash
# View scheduler logs
tail -f nohup.out

# Check Flask logs
journalctl -u gunicorn -f
```

## 💰 Stripe Pricing Setup

1. Go to Stripe Dashboard > Products
2. Create product: "Contractor Leads Monthly"
3. Add pricing: $20/month recurring
4. Copy Price ID (starts with `price_`)
5. Update `.env` with `STRIPE_PRICE_ID`

## 🔐 Security

- Keep `.env` and `firebase-credentials.json` private
- Use strong `SECRET_KEY` for Flask sessions
- Enable Firebase security rules
- Use Stripe webhook signing
- Implement rate limiting on API endpoints
- Add CSRF protection for production

## 📝 License

Proprietary - All rights reserved

## 🤝 Support

For issues or questions:
- Email: support@contractorleads.com
- Check Firebase/Stripe logs for errors

---

**Built with Python, Flask, BeautifulSoup, HuggingFace, Firebase, and Stripe**
# Force redeploy
