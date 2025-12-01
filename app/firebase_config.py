# app/firebase_config.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, db, auth
from datetime import datetime
from typing import Dict, Any, Optional

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with credentials"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        print("✅ Firebase already initialized")
    except ValueError:
        # Initialize with service account or environment variables
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": "innoventure-global",
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("FIREBASE_CERT_URL")
        })
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://innoventure-global-default-rtdb.firebaseio.com'
        })
        print("✅ Firebase initialized successfully")

# Initialize on module import
initialize_firebase()

# Firestore client
firestore_db = firestore.client()

# Realtime Database reference
realtime_db = db.reference()


class FirebaseService:
    """Service class for Firebase operations"""
    
    @staticmethod
    def create_campaign(user_id: str, campaign_data: Dict[str, Any]) -> str:
        """
        Create a new campaign in Firestore
        Returns: campaign_id
        """
        try:
            campaign_ref = firestore_db.collection('campaigns').document()
            campaign_id = campaign_ref.id
            
            campaign_doc = {
                'campaign_id': campaign_id,
                'user_id': user_id,
                'brand_name': campaign_data.get('brand_name'),
                'goal': campaign_data.get('goal'),
                'audience': campaign_data.get('audience'),
                'status': 'created',
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'posts': [],
                'execution_results': [],
                'report': None
            }
            
            campaign_ref.set(campaign_doc)
            print(f"✅ Campaign created in Firestore: {campaign_id}")
            return campaign_id
            
        except Exception as e:
            print(f"❌ Error creating campaign: {e}")
            raise
    
    @staticmethod
    def update_campaign_status(campaign_id: str, status: str, data: Optional[Dict] = None):
        """Update campaign status and data"""
        try:
            campaign_ref = firestore_db.collection('campaigns').document(campaign_id)
            
            update_data = {
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            if data:
                update_data.update(data)
            
            campaign_ref.update(update_data)
            print(f"✅ Campaign {campaign_id} updated to status: {status}")
            
        except Exception as e:
            print(f"❌ Error updating campaign: {e}")
            raise
    
    @staticmethod
    def save_campaign_posts(campaign_id: str, posts: list):
        """Save generated posts to campaign"""
        try:
            campaign_ref = firestore_db.collection('campaigns').document(campaign_id)
            campaign_ref.update({
                'posts': posts,
                'status': 'planned',
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            print(f"✅ Saved {len(posts)} posts for campaign {campaign_id}")
            
        except Exception as e:
            print(f"❌ Error saving posts: {e}")
            raise
    
    @staticmethod
    def save_execution_results(campaign_id: str, results: list):
        """Save execution results to campaign"""
        try:
            campaign_ref = firestore_db.collection('campaigns').document(campaign_id)
            campaign_ref.update({
                'execution_results': results,
                'status': 'executed',
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            print(f"✅ Saved execution results for campaign {campaign_id}")
            
        except Exception as e:
            print(f"❌ Error saving execution results: {e}")
            raise
    
    @staticmethod
    def save_campaign_report(campaign_id: str, report: str):
        """Save final report to campaign"""
        try:
            campaign_ref = firestore_db.collection('campaigns').document(campaign_id)
            campaign_ref.update({
                'report': report,
                'status': 'completed',
                'completed_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            print(f"✅ Saved report for campaign {campaign_id}")
            
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            raise
    
    @staticmethod
    def get_campaign(campaign_id: str) -> Optional[Dict]:
        """Retrieve campaign data"""
        try:
            campaign_ref = firestore_db.collection('campaigns').document(campaign_id)
            campaign_doc = campaign_ref.get()
            
            if campaign_doc.exists:
                return campaign_doc.to_dict()
            return None
            
        except Exception as e:
            print(f"❌ Error retrieving campaign: {e}")
            raise
    
    @staticmethod
    def get_user_campaigns(user_id: str, limit: int = 10) -> list:
        """Get all campaigns for a user"""
        try:
            campaigns_ref = firestore_db.collection('campaigns')
            query = campaigns_ref.where('user_id', '==', user_id).order_by(
                'created_at', direction=firestore.Query.DESCENDING
            ).limit(limit)
            
            campaigns = []
            for doc in query.stream():
                campaigns.append(doc.to_dict())
            
            return campaigns
            
        except Exception as e:
            print(f"❌ Error retrieving user campaigns: {e}")
            raise
    
    @staticmethod
    def log_campaign_activity(campaign_id: str, activity: str, details: Dict = None):
        """Log campaign activity to Realtime Database for real-time updates"""
        try:
            activity_ref = realtime_db.child('campaign_activities').child(campaign_id)
            activity_data = {
                'timestamp': datetime.now().isoformat(),
                'activity': activity,
                'details': details or {}
            }
            activity_ref.push(activity_data)
            print(f"✅ Logged activity for campaign {campaign_id}: {activity}")
            
        except Exception as e:
            print(f"❌ Error logging activity: {e}")
    
    @staticmethod
    def verify_user_token(id_token: str) -> Optional[Dict]:
        """Verify Firebase ID token and return user info"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name')
            }
        except Exception as e:
            print(f"❌ Error verifying token: {e}")
            return None
    
    @staticmethod
    def create_user_profile(user_id: str, user_data: Dict):
        """Create or update user profile in Firestore"""
        try:
            user_ref = firestore_db.collection('users').document(user_id)
            user_doc = {
                'user_id': user_id,
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'campaigns_count': 0
            }
            user_ref.set(user_doc, merge=True)
            print(f"✅ User profile created/updated: {user_id}")
            
        except Exception as e:
            print(f"❌ Error creating user profile: {e}")
            raise
    
    @staticmethod
    def increment_user_campaigns(user_id: str):
        """Increment user's campaign count"""
        try:
            user_ref = firestore_db.collection('users').document(user_id)
            user_ref.update({
                'campaigns_count': firestore.Increment(1),
                'updated_at': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            print(f"❌ Error incrementing campaign count: {e}")


# Export service instance
firebase_service = FirebaseService()