"""
Analytics and reporting endpoints
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.core.logging import get_logger
from app.services.database_service import database_service
from app.services.ml_service import ml_classifier
from app.models.responses import ErrorResponse, ErrorDetail

logger = get_logger("analytics_api")

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_financial_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
):
    """Get comprehensive financial summary for specified period"""
    try:
        summary = await database_service.get_financial_summary(days)
        
        if not summary:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NO_DATA",
                    "message": f"No financial data found for the last {days} days"
                }
            )
        
        return {
            "success": True,
            "data": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get financial summary: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ANALYSIS_ERROR",
                "message": "Failed to generate financial summary"
            }
        )


@router.get("/insights")
async def get_spending_insights():
    """Get advanced spending insights and patterns"""
    try:
        insights = await database_service.get_spending_insights()
        
        return {
            "success": True,
            "data": insights,
            "insights": {
                "recommendations": _generate_recommendations(insights),
                "alerts": _generate_alerts(insights)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get spending insights: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INSIGHTS_ERROR",
                "message": "Failed to generate spending insights"
            }
        )


@router.get("/transactions")
async def get_transaction_history(
    limit: int = Query(default=50, ge=1, le=500, description="Number of transactions to return"),
    offset: int = Query(default=0, ge=0, description="Number of transactions to skip"),
    category: Optional[str] = Query(default=None, description="Filter by category")
):
    """Get paginated transaction history with optional filtering"""
    try:
        transactions = await database_service.get_transaction_history(limit, offset)
        
        # Filter by category if specified
        if category:
            transactions = [t for t in transactions if t.get('category') == category]
        
        return {
            "success": True,
            "data": {
                "transactions": transactions,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": len(transactions)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get transaction history: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "HISTORY_ERROR",
                "message": "Failed to retrieve transaction history"
            }
        )


@router.get("/accuracy")
async def get_accuracy_metrics():
    """Get model accuracy metrics based on user feedback"""
    try:
        metrics = await database_service.get_accuracy_metrics()
        ml_stats = await ml_classifier.get_model_stats()
        
        return {
            "success": True,
            "data": {
                "accuracy_metrics": metrics,
                "ml_model_stats": ml_stats,
                "recommendations": _generate_accuracy_recommendations(metrics)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get accuracy metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "METRICS_ERROR",
                "message": "Failed to retrieve accuracy metrics"
            }
        )


@router.post("/train-model")
async def train_ml_model():
    """Train the machine learning model with current data"""
    try:
        result = await ml_classifier.train_model()
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "TRAINING_FAILED",
                    "message": result.get("message", "Model training failed"),
                    "details": result
                }
            )
        
        return {
            "success": True,
            "message": "Model trained successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to train ML model: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TRAINING_ERROR",
                "message": "Failed to train machine learning model"
            }
        )


@router.get("/categories/performance")
async def get_category_performance():
    """Get performance metrics for each transaction category"""
    try:
        # Get accuracy by category
        accuracy_metrics = await database_service.get_accuracy_metrics()
        
        # Get feature importance from ML model
        feature_importance = ml_classifier.get_feature_importance()
        
        return {
            "success": True,
            "data": {
                "category_accuracy": accuracy_metrics.get("most_corrected_categories", []),
                "feature_importance": feature_importance,
                "model_performance": {
                    "is_trained": ml_classifier.is_trained,
                    "supported_categories": ml_classifier.categories
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get category performance: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PERFORMANCE_ERROR",
                "message": "Failed to retrieve category performance metrics"
            }
        )


def _generate_recommendations(insights: dict) -> list:
    """Generate spending recommendations based on insights"""
    recommendations = []
    
    try:
        top_categories = insights.get("top_categories", [])
        daily_spending = insights.get("daily_spending", [])
        
        # High spending category recommendation
        if top_categories:
            highest_category = top_categories[0]
            if highest_category["amount"] > 1000:  # Threshold for high spending
                recommendations.append({
                    "type": "high_spending",
                    "category": highest_category["category"],
                    "message": f"Your highest spending is in {highest_category['category']} "
                              f"({highest_category['amount']:.0f} EGP). Consider reviewing these expenses.",
                    "priority": "high"
                })
        
        # Spending pattern recommendation
        if daily_spending:
            amounts = [day["amount"] for day in daily_spending]
            if amounts:
                avg_daily = sum(amounts) / len(amounts)
                max_daily = max(amounts)
                
                if max_daily > avg_daily * 2:
                    recommendations.append({
                        "type": "irregular_spending",
                        "message": f"You had some high spending days. Your average is {avg_daily:.0f} EGP "
                                  f"but your highest day was {max_daily:.0f} EGP.",
                        "priority": "medium"
                    })
        
        # Budget recommendation
        if top_categories and len(top_categories) >= 3:
            total_top_3 = sum(cat["amount"] for cat in top_categories[:3])
            recommendations.append({
                "type": "budget_suggestion",
                "message": f"Your top 3 spending categories account for {total_top_3:.0f} EGP. "
                          "Consider setting monthly budgets for these categories.",
                "priority": "low"
            })
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
    
    return recommendations


def _generate_alerts(insights: dict) -> list:
    """Generate spending alerts based on patterns"""
    alerts = []
    
    try:
        daily_spending = insights.get("daily_spending", [])
        
        if daily_spending and len(daily_spending) >= 7:
            # Check for increasing trend in last 7 days
            recent_days = daily_spending[-7:]
            amounts = [day["amount"] for day in recent_days]
            
            # Simple trend detection
            if len(amounts) >= 3:
                recent_avg = sum(amounts[-3:]) / 3
                earlier_avg = sum(amounts[:3]) / 3
                
                if recent_avg > earlier_avg * 1.5:
                    alerts.append({
                        "type": "spending_increase",
                        "message": "Your spending has increased significantly in the last few days.",
                        "severity": "warning"
                    })
        
    except Exception as e:
        logger.error(f"Failed to generate alerts: {e}")
    
    return alerts


def _generate_accuracy_recommendations(metrics: dict) -> list:
    """Generate recommendations for improving accuracy"""
    recommendations = []
    
    try:
        accuracy_rate = metrics.get("accuracy_rate", 0)
        total_feedback = metrics.get("total_feedback", 0)
        
        if accuracy_rate < 80 and total_feedback > 10:
            recommendations.append({
                "type": "accuracy_improvement",
                "message": f"Current accuracy is {accuracy_rate}%. Providing more feedback "
                          "will help improve the system's accuracy.",
                "action": "Correct misclassified transactions when you see them"
            })
        
        if total_feedback < 20:
            recommendations.append({
                "type": "feedback_needed",
                "message": "More user feedback is needed to train the machine learning model effectively.",
                "action": "Review and correct transaction classifications"
            })
        
        most_corrected = metrics.get("most_corrected_categories", [])
        if most_corrected:
            top_corrected = most_corrected[0]
            recommendations.append({
                "type": "category_improvement",
                "message": f"The '{top_corrected['category']}' category needs improvement "
                          f"({top_corrected['corrections']} corrections).",
                "action": f"Review {top_corrected['category']} classifications carefully"
            })
        
    except Exception as e:
        logger.error(f"Failed to generate accuracy recommendations: {e}")
    
    return recommendations