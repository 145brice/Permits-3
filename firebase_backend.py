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
            firebase_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if firebase_key:
                cred = credentials.Certificate(json.loads(firebase_key))
            elif config.FIREBASE_CREDENTIALS_PATH:
                cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
            else:
                # Fallback to individual environment variables
                cred = credentials.Certificate({
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
                })
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.auth = auth

    def create_user(self, email: str, password: str) -> Dict:
        """Create a new user in Firebase Auth"""
        try:
            user = self.auth.create_user(
                email=email,
                password=password
            )
            return {"success": True, "user_id": user.uid, "email": user.email}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_token(self, id_token: str) -> Optional[Dict]:
        """Verify Firebase ID token"""
        try:
            decoded_token = self.auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            return None

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user information by user ID"""
        try:
            user = self.auth.get_user(user_id)
            return {
                "user_id": user.uid,
                "email": user.email,
                "email_verified": user.email_verified,
                "disabled": user.disabled,
                "created_at": user.user_metadata.creation_timestamp,
                "last_sign_in": user.user_metadata.last_sign_in_timestamp
            }
        except Exception as e:
            return None

    def save_permit_data(self, user_id: str, permit_data: Dict) -> bool:
        """Save permit data to Firestore"""
        try:
            doc_ref = self.db.collection('permits').document(user_id)
            doc_ref.set({
                'user_id': user_id,
                'permit_data': permit_data,
                'timestamp': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error saving permit data: {e}")
            return False

    def get_permit_data(self, user_id: str) -> Optional[Dict]:
        """Retrieve permit data from Firestore"""
        try:
            doc_ref = self.db.collection('permits').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error retrieving permit data: {e}")
            return None

    def get_daily_leads(self, date_str: str) -> List[Dict]:
        """Get daily leads for a specific date (mock data for demo)"""
        # Mock data for demonstration
        return [
            {
                "county": "Nashville-Davidson",
                "permit_number": "DEMO-001",
                "address": "123 Main St, Nashville, TN",
                "permit_type": "Residential Addition",
                "estimated_value": 50000,
                "work_description": "Kitchen remodel and addition",
                "date": date_str
            },
            {
                "county": "Davidson",
                "permit_number": "DEMO-002",
                "address": "456 Oak Ave, Nashville, TN",
                "permit_type": "New Construction",
                "estimated_value": 250000,
                "work_description": "Single family home construction",
                "date": date_str
            }
        ]
