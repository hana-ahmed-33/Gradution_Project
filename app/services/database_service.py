"""
Database service for storing and retrieving financial data
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.core.logging import get_logger
from app.database.connection import get_db_session
from app.database.models import TransactionDB, AnalysisSessionDB, UserFeedbackDB
from app.models.domain import Transaction, TransactionType
from app.models.responses import AnalysisResult, FinancialSummary

logger = get_logger("database_service")


class DatabaseService:
    """Service for database operations"""
    
    async def save_analysis_result(self, result: AnalysisResult, session_type: str, 
                                 original_input: str, transcribed_text: str = None) -> str:
        """Save complete analysis result to database"""
        try:
            session_id = str(uuid.uuid4())
            
            with get_db_session() as db:
                # Save analysis session
                session_db = AnalysisSessionDB(
                    id=session_id,
                    session_type=session_type,
                    original_input=original_input,
                    transcribed_text=transcribed_text,
                    language_detected=result.language_detected,
                    total_transactions=result.summary.total_transactions,
                    total_income=result.summary.total_income,
                    total_expenses=result.summary.total_expenses,
                    net_amount=result.summary.net_amount,
                    processing_time_ms=result.processing_time_ms,
                    confidence_avg=self._calculate_avg_confidence(result.transactions)
                )
                db.add(session_db)
                
                # Save individual transactions
                for transaction in result.transactions:
                    transaction_db = TransactionDB(
                        id=transaction.id,
                        amount=transaction.amount,
                        transaction_type=TransactionType(transaction.transaction_type),
                        category=transaction.category,
                        item=transaction.item,
                        merchant=transaction.merchant,
                        confidence_score=transaction.confidence_score,
                        extracted_from=getattr(transaction, 'extracted_from', None) or getattr(transaction, 'extracted_text', None),
                        original_text=original_input,
                        language_detected=result.language_detected,
                        processing_time_ms=result.processing_time_ms
                    )
                    db.add(transaction_db)
                
                # commit is handled by the get_db_session context manager
                logger.info(f"Saved analysis result with {len(result.transactions)} transactions")
                return session_id
                
        except Exception as e:
            logger.error(f"Failed to save analysis result: {e}")
            raise
    
    async def get_transaction_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get transaction history"""
        try:
            with get_db_session() as db:
                transactions = db.query(TransactionDB)\
                    .order_by(desc(TransactionDB.created_at))\
                    .limit(limit)\
                    .offset(offset)\
                    .all()
                
                return [t.to_dict() for t in transactions]
                
        except Exception as e:
            logger.error(f"Failed to get transaction history: {e}")
            return []
    
    async def get_financial_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get financial summary for specified period"""
        try:
            with get_db_session() as db:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Get transactions in period
                transactions = db.query(TransactionDB)\
                    .filter(TransactionDB.created_at >= start_date)\
                    .all()
                
                # Calculate summary
                total_income = sum(t.amount or 0 for t in transactions 
                                 if t.transaction_type == TransactionType.INCOME)
                total_expenses = sum(t.amount or 0 for t in transactions 
                                   if t.transaction_type == TransactionType.EXPENSE)
                
                # Category breakdown
                categories = {}
                for t in transactions:
                    if t.category and t.amount:
                        categories[t.category] = categories.get(t.category, 0) + t.amount
                
                # Monthly trends
                monthly_data = self._get_monthly_trends(db, start_date)
                
                return {
                    "period_days": days,
                    "total_transactions": len(transactions),
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "net_amount": total_income - total_expenses,
                    "categories": categories,
                    "monthly_trends": monthly_data,
                    "avg_transaction_amount": sum(t.amount or 0 for t in transactions) / len(transactions) if transactions else 0,
                    "most_frequent_category": max(categories.items(), key=lambda x: x[1])[0] if categories else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get financial summary: {e}")
            return {}
    
    async def get_spending_insights(self) -> Dict[str, Any]:
        """Get advanced spending insights"""
        try:
            with get_db_session() as db:
                # Last 30 days
                start_date = datetime.utcnow() - timedelta(days=30)
                
                # Top spending categories
                category_spending = db.query(
                    TransactionDB.category,
                    func.sum(TransactionDB.amount).label('total'),
                    func.count(TransactionDB.id).label('count')
                ).filter(
                    and_(
                        TransactionDB.created_at >= start_date,
                        TransactionDB.transaction_type == TransactionType.EXPENSE,
                        TransactionDB.amount.isnot(None)
                    )
                ).group_by(TransactionDB.category)\
                .order_by(desc('total'))\
                .limit(10).all()
                
                # Top merchants
                merchant_spending = db.query(
                    TransactionDB.merchant,
                    func.sum(TransactionDB.amount).label('total'),
                    func.count(TransactionDB.id).label('count')
                ).filter(
                    and_(
                        TransactionDB.created_at >= start_date,
                        TransactionDB.transaction_type == TransactionType.EXPENSE,
                        TransactionDB.merchant.isnot(None),
                        TransactionDB.amount.isnot(None)
                    )
                ).group_by(TransactionDB.merchant)\
                .order_by(desc('total'))\
                .limit(10).all()
                
                # Daily spending pattern
                daily_spending = db.query(
                    func.date(TransactionDB.created_at).label('date'),
                    func.sum(TransactionDB.amount).label('total')
                ).filter(
                    and_(
                        TransactionDB.created_at >= start_date,
                        TransactionDB.transaction_type == TransactionType.EXPENSE,
                        TransactionDB.amount.isnot(None)
                    )
                ).group_by(func.date(TransactionDB.created_at))\
                .order_by('date').all()
                
                return {
                    "top_categories": [
                        {"category": cat, "amount": float(total), "count": count}
                        for cat, total, count in category_spending
                    ],
                    "top_merchants": [
                        {"merchant": merchant, "amount": float(total), "count": count}
                        for merchant, total, count in merchant_spending
                    ],
                    "daily_spending": [
                        {"date": date.isoformat(), "amount": float(total)}
                        for date, total in daily_spending
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get spending insights: {e}")
            return {}
    
    async def save_user_feedback(self, transaction_id: str, feedback_data: Dict[str, Any]) -> str:
        """Save user feedback for improving accuracy"""
        try:
            feedback_id = str(uuid.uuid4())
            
            with get_db_session() as db:
                feedback = UserFeedbackDB(
                    id=feedback_id,
                    transaction_id=transaction_id,
                    original_category=feedback_data.get('original_category'),
                    corrected_category=feedback_data.get('corrected_category'),
                    original_item=feedback_data.get('original_item'),
                    corrected_item=feedback_data.get('corrected_item'),
                    original_amount=feedback_data.get('original_amount'),
                    corrected_amount=feedback_data.get('corrected_amount'),
                    feedback_type=feedback_data.get('feedback_type', 'correction'),
                    user_comment=feedback_data.get('comment')
                )
                db.add(feedback)
                # commit is handled by the get_db_session context manager
                
                logger.info(f"Saved user feedback for transaction {transaction_id}")
                return feedback_id
                
        except Exception as e:
            logger.error(f"Failed to save user feedback: {e}")
            raise
    
    async def get_accuracy_metrics(self) -> Dict[str, Any]:
        """Get accuracy metrics based on user feedback"""
        try:
            with get_db_session() as db:
                total_feedback = db.query(UserFeedbackDB).count()
                corrections = db.query(UserFeedbackDB)\
                    .filter(UserFeedbackDB.feedback_type == 'correction').count()
                confirmations = db.query(UserFeedbackDB)\
                    .filter(UserFeedbackDB.feedback_type == 'confirmation').count()
                
                accuracy_rate = (confirmations / total_feedback * 100) if total_feedback > 0 else 0
                
                # Most corrected categories
                category_corrections = db.query(
                    UserFeedbackDB.original_category,
                    func.count(UserFeedbackDB.id).label('count')
                ).filter(UserFeedbackDB.feedback_type == 'correction')\
                .group_by(UserFeedbackDB.original_category)\
                .order_by(desc('count'))\
                .limit(5).all()
                
                return {
                    "total_feedback": total_feedback,
                    "corrections": corrections,
                    "confirmations": confirmations,
                    "accuracy_rate": round(accuracy_rate, 2),
                    "most_corrected_categories": [
                        {"category": cat, "corrections": count}
                        for cat, count in category_corrections
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get accuracy metrics: {e}")
            return {}
    
    def _calculate_avg_confidence(self, transactions: List) -> float:
        """Calculate average confidence score"""
        if not transactions:
            return 0.0
        
        total_confidence = sum(t.confidence_score or 0 for t in transactions)
        return total_confidence / len(transactions)
    
    def _get_monthly_trends(self, db: Session, start_date: datetime) -> List[Dict]:
        """Get monthly spending trends"""
        try:
            monthly_data = db.query(
                func.strftime('%Y-%m', TransactionDB.created_at).label('month'),
                func.sum(TransactionDB.amount).label('total'),
                TransactionDB.transaction_type
            ).filter(
                and_(
                    TransactionDB.created_at >= start_date,
                    TransactionDB.amount.isnot(None)
                )
            ).group_by('month', TransactionDB.transaction_type)\
            .order_by('month').all()
            
            # Organize by month
            trends = {}
            for month, total, trans_type in monthly_data:
                if month not in trends:
                    trends[month] = {"month": month, "income": 0, "expenses": 0}
                
                if trans_type == TransactionType.INCOME:
                    trends[month]["income"] = float(total)
                else:
                    trends[month]["expenses"] = float(total)
            
            return list(trends.values())
            
        except Exception as e:
            logger.error(f"Failed to get monthly trends: {e}")
            return []


# Global database service instance
database_service = DatabaseService()