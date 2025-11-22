"""
Stripe payment integration
"""
import stripe
from typing import Dict, Optional
import config

stripe.api_key = config.STRIPE_SECRET_KEY


class StripePayment:
    """Handle Stripe subscription payments"""
    
    def __init__(self):
        # County-specific price IDs - all $49.99/month
        self.price_ids = {
            'tennessee_nashville': 'price_nashville_4999',  # $49.99/month for Nashville
            'tennessee_hamilton': 'price_hamilton_4999',   # $49.99/month for Chattanooga
            'texas_bexar': 'price_bexar_4999',             # $49.99/month for San Antonio
            'texas_travis': 'price_travis_4999',           # $49.99/month for Austin
        }
        self.default_price_id = config.STRIPE_PRICE_ID  # Fallback
    
    def create_checkout_session(self, customer_email: str, user_id: str) -> Dict:
        """Create a Stripe Checkout session for subscription"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='subscription',
                customer_email=customer_email,
                line_items=[{
                    'price': self.price_id,
                    'quantity': 1,
                }],
                success_url='http://localhost:5008/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://yourapp.com/cancel',
                metadata={
                    'user_id': user_id
                }
            )
            
            return {
                'session_id': session.id,
                'url': session.url
            }
        
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None
    
    def create_customer_portal_session(self, customer_id: str) -> Dict:
        """Create a portal session for subscription management"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url='https://yourapp.com/dashboard'
            )
            
            return {'url': session.url}
        
        except Exception as e:
            print(f"Error creating portal session: {e}")
            return None
    
    def get_subscription_status(self, subscription_id: str) -> Optional[str]:
        """Get current subscription status"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription.status
        except Exception as e:
            print(f"Error getting subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        try:
            stripe.Subscription.delete(subscription_id)
            return True
        except Exception as e:
            print(f"Error canceling subscription: {e}")
            return False
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, config.STRIPE_WEBHOOK_SECRET
            )
            
            event_type = event['type']
            event_data = event['data']['object']
            
            result = {
                'type': event_type,
                'data': {}
            }
            
            if event_type == 'checkout.session.completed':
                result['data'] = {
                    'customer_id': event_data.get('customer'),
                    'subscription_id': event_data.get('subscription'),
                    'user_id': event_data.get('metadata', {}).get('user_id')
                }
            
            elif event_type == 'customer.subscription.updated':
                result['data'] = {
                    'subscription_id': event_data['id'],
                    'status': event_data['status'],
                    'customer_id': event_data['customer']
                }
            
            elif event_type == 'customer.subscription.deleted':
                result['data'] = {
                    'subscription_id': event_data['id'],
                    'customer_id': event_data['customer']
                }
            
            return result
        
        except Exception as e:
            print(f"Error handling webhook: {e}")
            return None
