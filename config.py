"""
Configuration module for Contractor Leads SaaS
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Firebase
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')

# Firebase credentials from environment variables (for Railway deployment)
FIREBASE_TYPE = os.getenv('FIREBASE_TYPE')
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_PRIVATE_KEY_ID = os.getenv('FIREBASE_PRIVATE_KEY_ID')
FIREBASE_PRIVATE_KEY = os.getenv('FIREBASE_PRIVATE_KEY')
FIREBASE_CLIENT_EMAIL = os.getenv('FIREBASE_CLIENT_EMAIL')
FIREBASE_CLIENT_ID = os.getenv('FIREBASE_CLIENT_ID')
FIREBASE_AUTH_URI = os.getenv('FIREBASE_AUTH_URI')
FIREBASE_TOKEN_URI = os.getenv('FIREBASE_TOKEN_URI')
FIREBASE_AUTH_PROVIDER_X509_CERT_URL = os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL')
FIREBASE_CLIENT_X509_CERT_URL = os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
FIREBASE_UNIVERSE_DOMAIN = os.getenv('FIREBASE_UNIVERSE_DOMAIN')

# Stripe
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID = os.getenv('STRIPE_PRICE_ID')

# Stripe Payment Links (Live)
STRIPE_LINK_NASHVILLE = os.getenv('STRIPE_LINK_NASHVILLE', 'https://buy.stripe.com/3cI00laXCauv722h1B63K0q')
STRIPE_LINK_CHATTANOOGA = os.getenv('STRIPE_LINK_CHATTANOOGA', 'https://buy.stripe.com/dRmeVf0iYgST2LM9z963K0p')
STRIPE_LINK_AUSTIN = os.getenv('STRIPE_LINK_AUSTIN', 'https://buy.stripe.com/4gM5kF0iY0TVgCC12D63K0n')
STRIPE_LINK_SANANTONIO = os.getenv('STRIPE_LINK_SANANTONIO', 'https://buy.stripe.com/8x25kF9TygST8663aL63K0o')

# Email
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
FROM_EMAIL = os.getenv('FROM_EMAIL')

# Flask
SECRET_KEY = os.getenv('SECRET_KEY')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
PORT = int(os.getenv('PORT', 8003))

# AI Model
HF_MODEL_NAME = os.getenv('HF_MODEL_NAME', 'distilbert-base-uncased-finetuned-sst-2-english')

# Scraping
SCRAPE_TIME = os.getenv('SCRAPE_TIME', '02:00')

# County websites
COUNTY_URLS = {
    'nashville_davidson': 'https://www.nashville.gov/departments/codes/building-permits',
    'rutherford': 'https://www.rutherfordcountytn.gov/building_codes',
    'wilson': 'https://www.wilsoncountytn.gov/building',
    'sumner': 'https://www.sumnercountytn.gov/building'
}
