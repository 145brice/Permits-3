"""
Firebase backend integration
"""
import firebase_admin
from firebase_admin import credentials, firestore, auth
from typing import Dict, List, Optional
from datetime import datetime
import config
import json
import os


class FirebaseBackend:
    """Manages Firebase authentication and database operations"""
    
    def __init__(self):
        """Initialize Firebase app"""
        if not firebase_admin._apps:
            # Try FIREBASE_KEY environment variable first (single JSON string)
            firebase_key = os.getenv('FIREBASE_KEY')
            if firebase_key:
                cred_dict = json.loads(firebase_key)
                cred = credentials.Certificate(cred_dict)
            # Fallback to individual environment variables
            elif config.FIREBASE_TYPE and config.FIREBASE_PRIVATE_KEY:
                cred_dict = {
                    "type": config.FIREBASE_TYPE,
                    "project_id": config.FIREBASE_PROJECT_ID,
                    "private_key_id": config.FIREBASE_PRIVATE_KEY_ID,
                    "private_key": config.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
                    "client_email": config.FIREBASE_CLIENT_EMAIL,
                    "client_id": config.FIREBASE_CLIENT_ID,
                    "auth_uri": config.FIREBASE_AUTH_URI,
                    "token_uri": config.FIREBASE_TOKEN_URI,
                    "auth_provider_x509_cert_url": config.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
                    "client_x509_cert_url": config.FIREBASE_CLIENT_X509_CERT_URL,
                    "universe_domain": config.FIREBASE_UNIVERSE_DOMAIN
                }
                cred = credentials.Certificate(cred_dict)
            elif config.FIREBASE_CREDENTIALS_PATH:
                cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
            else:
                raise ValueError("Firebase credentials not configured. Set FIREBASE_KEY environment variable or individual FIREBASE_* environment variables.")
            
            options = {}
            if config.FIREBASE_DATABASE_URL:
                options['databaseURL'] = config.FIREBASE_DATABASE_URL
            firebase_admin.initialize_app(cred, options)
        
        self.db = firestore.client()
    
    # User Management
    def create_user(self, email: str, password: str) -> Dict:
        """Create a new user account"""
        try:
            user = auth.create_user(
                email=email,
                password=password
            )
            
            # Create user document
            user_data = {
                'email': email,
                'created_at': datetime.now(),
                'subscription_status': 'inactive',
                'stripe_customer_id': None
            }
            
            self.db.collection('users').document(user.uid).set(user_data)
            
            return {'uid': user.uid, 'email': email}
        
        except Exception as e:
            print(f"Error creating user: {e}")
            return {'error': str(e)}
    
    def get_user(self, uid: str) -> Optional[Dict]:
        """Get user data by UID"""
        try:
            doc = self.db.collection('users').document(uid).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_user_subscription(self, uid: str, stripe_customer_id: str, 
                                  subscription_id: str, status: str):
        """Update user subscription status"""
        try:
            self.db.collection('users').document(uid).update({
                'stripe_customer_id': stripe_customer_id,
                'subscription_id': subscription_id,
                'subscription_status': status,
                'updated_at': datetime.now()
            })
        except Exception as e:
            print(f"Error updating subscription: {e}")
    
    # Permit Management
    def save_permits(self, permits: List[Dict], batch_id: str):
        """Save scraped permits to database"""
        try:
            batch = self.db.batch()
            
            for permit in permits:
                permit['batch_id'] = batch_id
                permit['created_at'] = datetime.now()
                
                # Create unique ID from permit number and county
                doc_id = f"{permit['county']}_{permit['permit_number']}".replace(' ', '_')
                doc_ref = self.db.collection('permits').document(doc_id)
                
                batch.set(doc_ref, permit)
            
            batch.commit()
            print(f"Saved {len(permits)} permits with batch_id: {batch_id}")
        
        except Exception as e:
            print(f"Error saving permits: {e}")
    
    def get_recent_permits(self, days: int = 1) -> List[Dict]:
        """Get permits from recent days"""
        try:
            cutoff_date = datetime.now()
            
            permits_ref = self.db.collection('permits')\
                .where('created_at', '>=', cutoff_date)\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(500)
            
            docs = permits_ref.stream()
            return [doc.to_dict() for doc in docs]
        
        except Exception as e:
            print(f"Error getting recent permits: {e}")
            return []
    
    def get_active_subscribers(self) -> List[Dict]:
        """Get all users with active subscriptions"""
        try:
            users_ref = self.db.collection('users')\
                .where('subscription_status', '==', 'active')
            
            docs = users_ref.stream()
            return [{'uid': doc.id, **doc.to_dict()} for doc in docs]
        
        except Exception as e:
            print(f"Error getting subscribers: {e}")
            return []
    
    def get_last_scrape_date(self) -> str:
        """Get the last date scraping was performed"""
        try:
            doc = self.db.collection('system').document('scraper_status').get()
            if doc.exists:
                data = doc.to_dict()
                return data.get('last_scrape_date', '')
            return ''
        except Exception as e:
            print(f"Error getting last scrape date: {e}")
            return ''
    
    def update_last_scrape_date(self, date: str):
        """Update the last scrape date"""
        try:
            self.db.collection('system').document('scraper_status').set({
                'last_scrape_date': date,
                'updated_at': datetime.now()
            }, merge=True)
        except Exception as e:
            print(f"Error updating last scrape date: {e}")
    
    # Lead History
    def save_daily_leads(self, date: str, leads: List[Dict]):
        """Save top leads for a specific date"""
        try:
            doc_ref = self.db.collection('daily_leads').document(date)
            doc_ref.set({
                'date': date,
                'leads': leads,
                'created_at': datetime.now()
            })
        except Exception as e:
            print(f"Error saving daily leads: {e}")
    
    def get_daily_leads(self, date: str) -> List[Dict]:
        """Get top leads for a specific date"""
        try:
            doc = self.db.collection('daily_leads').document(date).get()
            if doc.exists:
                return doc.to_dict().get('leads', [])
            return []
        except Exception as e:
            print(f"Error getting daily leads: {e}")
            return []
