"""
Solana Payment Integration for CoreSense Premium Features
Handles cryptocurrency payments through Solana blockchain
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

@dataclass
class SolanaWallet:
    """Represents a Solana wallet configuration"""
    public_key: str
    private_key: Optional[str] = None  # Never log or expose this
    network: str = "mainnet-beta"
    
@dataclass
class PaymentPlan:
    """Represents a CoreSense payment plan"""
    plan_id: str
    name: str
    price_usd: float
    price_sol: float
    duration_days: int
    features: List[str]
    agent_access: List[str]

@dataclass
class PaymentTransaction:
    """Represents a payment transaction"""
    transaction_id: str
    user_id: str
    plan_id: str
    amount_sol: float
    amount_usd: float
    wallet_address: str
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    transaction_hash: Optional[str] = None

class SolanaPaymentService:
    """Service for handling Solana payments for CoreSense premium features"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sol_to_usd_rate = 23.50  # Approximate SOL price - would fetch from API in production
        
        # CoreSense payment plans
        self.payment_plans = {
            "basic": PaymentPlan(
                plan_id="basic",
                name="CoreSense Basic",
                price_usd=29.99,
                price_sol=1.28,
                duration_days=30,
                features=[
                    "Basic muscle activation analysis",
                    "Real-time feedback",
                    "Progress tracking",
                    "5 AI coaching sessions/month"
                ],
                agent_access=["coresense-fabric-sensor"]
            ),
            "pro": PaymentPlan(
                plan_id="pro", 
                name="CoreSense Pro",
                price_usd=49.99,
                price_sol=2.13,
                duration_days=30,
                features=[
                    "Advanced muscle activation analysis",
                    "Real-time feedback",
                    "Detailed progress analytics",
                    "Unlimited AI coaching",
                    "Compensation detection",
                    "Custom workout plans",
                    "Priority support"
                ],
                agent_access=["coresense-fabric-sensor", "coresense-ai-coach"]
            ),
            "enterprise": PaymentPlan(
                plan_id="enterprise",
                name="CoreSense Enterprise",
                price_usd=199.99,
                price_sol=8.51,
                duration_days=30,
                features=[
                    "All Pro features",
                    "Multi-agent orchestration",
                    "Team management",
                    "API access",
                    "Custom integrations",
                    "Advanced analytics",
                    "Dedicated support",
                    "External agent marketplace access"
                ],
                agent_access=["coresense-fabric-sensor", "coresense-ai-coach", "coresense-orchestrator"]
            )
        }
        
        # CoreSense treasury wallet (simulation)
        self.treasury_wallet = SolanaWallet(
            public_key="CoreSenseTreasuryWalletPublicKeyHere123456789",
            network="mainnet-beta"
        )
        
        self.transactions = {}
    
    def get_payment_plans(self) -> Dict[str, PaymentPlan]:
        """Get all available payment plans"""
        return self.payment_plans
    
    def calculate_sol_price(self, usd_amount: float) -> float:
        """Calculate SOL amount from USD"""
        return round(usd_amount / self.sol_to_usd_rate, 6)
    
    def calculate_usd_price(self, sol_amount: float) -> float:
        """Calculate USD amount from SOL"""
        return round(sol_amount * self.sol_to_usd_rate, 2)
    
    async def create_payment_request(self, 
                                   user_id: str, 
                                   plan_id: str,
                                   user_wallet: str) -> Dict[str, Any]:
        """Create a payment request for a subscription plan"""
        try:
            if plan_id not in self.payment_plans:
                return {"success": False, "error": "Invalid payment plan"}
            
            plan = self.payment_plans[plan_id]
            transaction_id = f"coresense_{user_id}_{plan_id}_{datetime.now().timestamp()}"
            
            # Create payment transaction
            transaction = PaymentTransaction(
                transaction_id=transaction_id,
                user_id=user_id,
                plan_id=plan_id,
                amount_sol=plan.price_sol,
                amount_usd=plan.price_usd,
                wallet_address=user_wallet,
                status="pending",
                created_at=datetime.now()
            )
            
            self.transactions[transaction_id] = transaction
            
            # Create Solana payment request
            payment_request = {
                "success": True,
                "transaction_id": transaction_id,
                "payment_details": {
                    "recipient": self.treasury_wallet.public_key,
                    "amount": plan.price_sol,
                    "currency": "SOL",
                    "memo": f"CoreSense {plan.name} subscription",
                    "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat()
                },
                "plan_details": {
                    "name": plan.name,
                    "features": plan.features,
                    "duration_days": plan.duration_days,
                    "agent_access": plan.agent_access
                },
                "qr_code_data": self._generate_qr_data(plan.price_sol, transaction_id),
                "payment_url": f"solana:{self.treasury_wallet.public_key}?amount={plan.price_sol}&memo=CoreSense-{transaction_id}"
            }
            
            self.logger.info(f"Payment request created for user {user_id}, plan {plan_id}")
            return payment_request
            
        except Exception as e:
            self.logger.error(f"Failed to create payment request: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_qr_data(self, amount: float, transaction_id: str) -> str:
        """Generate QR code data for payment"""
        return f"solana:{self.treasury_wallet.public_key}?amount={amount}&memo=CoreSense-{transaction_id}"
    
    async def verify_payment(self, transaction_id: str, 
                           blockchain_hash: str) -> Dict[str, Any]:
        """Verify a payment transaction on Solana blockchain"""
        try:
            if transaction_id not in self.transactions:
                return {"success": False, "error": "Transaction not found"}
            
            transaction = self.transactions[transaction_id]
            
            # Simulate blockchain verification
            # In production, this would query Solana blockchain for the transaction
            verification_result = await self._simulate_blockchain_verification(
                blockchain_hash, transaction.amount_sol
            )
            
            if verification_result["verified"]:
                # Update transaction status
                transaction.status = "confirmed"
                transaction.confirmed_at = datetime.now()
                transaction.transaction_hash = blockchain_hash
                
                # Activate subscription
                subscription = await self._activate_subscription(transaction)
                
                response = {
                    "success": True,
                    "transaction_verified": True,
                    "subscription_activated": True,
                    "subscription_details": subscription,
                    "transaction_hash": blockchain_hash,
                    "confirmed_at": transaction.confirmed_at.isoformat()
                }
                
                self.logger.info(f"Payment verified and subscription activated for transaction {transaction_id}")
                return response
            else:
                return {"success": False, "error": "Payment verification failed"}
                
        except Exception as e:
            self.logger.error(f"Failed to verify payment: {e}")
            return {"success": False, "error": str(e)}
    
    async def _simulate_blockchain_verification(self, 
                                              tx_hash: str, 
                                              expected_amount: float) -> Dict[str, Any]:
        """Simulate blockchain transaction verification"""
        # In production, this would query actual Solana blockchain
        await asyncio.sleep(0.5)  # Simulate network delay
        
        return {
            "verified": True,
            "amount": expected_amount,
            "confirmations": 32,
            "block_height": 285432109,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _activate_subscription(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Activate user subscription after successful payment"""
        plan = self.payment_plans[transaction.plan_id]
        
        subscription = {
            "subscription_id": f"sub_{transaction.transaction_id}",
            "user_id": transaction.user_id,
            "plan_id": transaction.plan_id,
            "plan_name": plan.name,
            "features_enabled": plan.features,
            "agent_access": plan.agent_access,
            "activated_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=plan.duration_days)).isoformat(),
            "status": "active",
            "payment_transaction": transaction.transaction_id
        }
        
        return subscription
    
    async def check_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Check user's subscription status"""
        try:
            # Find user's active subscription
            active_subscription = None
            for tx_id, transaction in self.transactions.items():
                if (transaction.user_id == user_id and 
                    transaction.status == "confirmed"):
                    
                    plan = self.payment_plans[transaction.plan_id]
                    expiry = transaction.confirmed_at + timedelta(days=plan.duration_days)
                    
                    if expiry > datetime.now():
                        active_subscription = {
                            "subscription_id": f"sub_{tx_id}",
                            "plan_id": transaction.plan_id,
                            "plan_name": plan.name,
                            "features": plan.features,
                            "agent_access": plan.agent_access,
                            "expires_at": expiry.isoformat(),
                            "status": "active",
                            "days_remaining": (expiry - datetime.now()).days
                        }
                        break
            
            if active_subscription:
                return {"success": True, "subscription": active_subscription}
            else:
                return {"success": True, "subscription": None, "message": "No active subscription"}
                
        except Exception as e:
            self.logger.error(f"Failed to check subscription status: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_payment_history(self, user_id: str) -> Dict[str, Any]:
        """Get payment history for a user"""
        try:
            user_transactions = []
            for transaction in self.transactions.values():
                if transaction.user_id == user_id:
                    plan = self.payment_plans[transaction.plan_id]
                    user_transactions.append({
                        "transaction_id": transaction.transaction_id,
                        "plan_name": plan.name,
                        "amount_sol": transaction.amount_sol,
                        "amount_usd": transaction.amount_usd,
                        "status": transaction.status,
                        "created_at": transaction.created_at.isoformat(),
                        "confirmed_at": transaction.confirmed_at.isoformat() if transaction.confirmed_at else None,
                        "transaction_hash": transaction.transaction_hash
                    })
            
            return {
                "success": True,
                "transactions": sorted(user_transactions, 
                                     key=lambda x: x["created_at"], 
                                     reverse=True)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get payment history: {e}")
            return {"success": False, "error": str(e)}
    
    def get_agent_earnings(self, agent_id: str, timeframe: str = "30d") -> Dict[str, Any]:
        """Calculate earnings for an agent from premium subscriptions"""
        try:
            # Revenue sharing model: agents get 70% of subscription revenue
            revenue_share = 0.70
            
            # Simulate earnings calculation
            total_subscriptions = 0
            total_revenue_sol = 0.0
            
            for transaction in self.transactions.values():
                if transaction.status == "confirmed":
                    plan = self.payment_plans[transaction.plan_id]
                    if agent_id in plan.agent_access:
                        total_subscriptions += 1
                        # Distribute revenue among agents in the plan
                        agent_share = transaction.amount_sol / len(plan.agent_access) * revenue_share
                        total_revenue_sol += agent_share
            
            earnings = {
                "agent_id": agent_id,
                "timeframe": timeframe,
                "total_subscriptions": total_subscriptions,
                "revenue_sol": round(total_revenue_sol, 6),
                "revenue_usd": round(total_revenue_sol * self.sol_to_usd_rate, 2),
                "revenue_share_percentage": revenue_share * 100,
                "calculated_at": datetime.now().isoformat()
            }
            
            return {"success": True, "earnings": earnings}
            
        except Exception as e:
            self.logger.error(f"Failed to calculate agent earnings: {e}")
            return {"success": False, "error": str(e)}

# Global payment service instance
solana_payment_service = SolanaPaymentService()