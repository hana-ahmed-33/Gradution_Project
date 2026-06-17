"""
Machine Learning service for improved transaction classification
"""
import json
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from app.core.logging import get_logger
from app.database.connection import get_db_session
from app.database.models import TransactionDB, UserFeedbackDB
from app.utils.text_utils import normalize_arabic_text

logger = get_logger("ml_service")


class MLTransactionClassifier:
    """Machine Learning classifier for transaction categorization"""
    
    def __init__(self):
        self.model = None
        self.categories = [
            'Food & Drinks', 'Transportation', 'Shopping', 'Health & Beauty',
            'Clothes & Fashion', 'Bills & Utilities', 'Entertainment', 'Salary & Income'
        ]
        self.model_path = "models/transaction_classifier.pkl"
        self.is_trained = False
        
        # Enhanced feature extraction
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words=None,  # Keep Arabic stop words
            lowercase=True,
            analyzer='word',
            token_pattern=r'(?u)\b\w+\b'
        )
        
        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', self.vectorizer),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        # Load existing model if available
        self._load_model()
    
    def prepare_training_data(self) -> Tuple[List[str], List[str]]:
        """Prepare training data from database and feedback"""
        texts = []
        labels = []
        
        try:
            with get_db_session() as db:
                # Get transactions with user feedback (corrected labels)
                feedback_data = db.query(UserFeedbackDB).all()
                feedback_corrections = {
                    f.transaction_id: f.corrected_category 
                    for f in feedback_data 
                    if f.corrected_category
                }
                
                # Get all transactions
                transactions = db.query(TransactionDB).all()
                
                for transaction in transactions:
                    if transaction.extracted_from and transaction.category:
                        text = self._prepare_text_features(transaction)
                        
                        # Use corrected category if available, otherwise original
                        category = feedback_corrections.get(transaction.id, transaction.category)
                        
                        if category in self.categories:
                            texts.append(text)
                            labels.append(category)
                
                logger.info(f"Prepared {len(texts)} training samples with {len(feedback_corrections)} corrections")
                return texts, labels
                
        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return [], []
    
    def _prepare_text_features(self, transaction: TransactionDB) -> str:
        """Prepare text features for ML model"""
        features = []
        
        # Original extracted text
        if transaction.extracted_from:
            features.append(normalize_arabic_text(transaction.extracted_from))
        
        # Merchant information
        if transaction.merchant:
            features.append(f"merchant_{transaction.merchant.lower()}")
        
        # Item information
        if transaction.item:
            features.append(f"item_{transaction.item.lower()}")
        
        # Amount range (categorical)
        if transaction.amount:
            if transaction.amount < 50:
                features.append("amount_small")
            elif transaction.amount < 200:
                features.append("amount_medium")
            elif transaction.amount < 500:
                features.append("amount_large")
            else:
                features.append("amount_very_large")
        
        # Transaction type
        if transaction.transaction_type:
            features.append(f"type_{transaction.transaction_type.value}")
        
        return " ".join(features)
    
    async def train_model(self, min_samples: int = 50) -> Dict[str, Any]:
        """Train the ML model with available data"""
        try:
            # Prepare training data
            texts, labels = self.prepare_training_data()
            
            if len(texts) < min_samples:
                logger.warning(f"Insufficient training data: {len(texts)} samples (minimum: {min_samples})")
                return {
                    "success": False,
                    "message": f"Need at least {min_samples} samples, got {len(texts)}",
                    "samples_count": len(texts)
                }
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42, stratify=labels
            )
            
            # Train model
            logger.info("Training ML classification model...")
            self.pipeline.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Detailed metrics
            report = classification_report(y_test, y_pred, output_dict=True)
            
            # Save model
            self._save_model()
            self.is_trained = True
            
            logger.info(f"Model trained successfully with accuracy: {accuracy:.3f}")
            
            return {
                "success": True,
                "accuracy": accuracy,
                "samples_count": len(texts),
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "classification_report": report,
                "categories": self.categories
            }
            
        except Exception as e:
            logger.error(f"Failed to train ML model: {e}")
            return {
                "success": False,
                "error": str(e),
                "samples_count": 0
            }
    
    def predict_category(self, text: str, merchant: str = None, 
                        item: str = None, amount: float = None) -> Tuple[str, float]:
        """Predict transaction category using ML model"""
        if not self.is_trained:
            logger.warning("ML model not trained, falling back to rule-based classification")
            return None, 0.0
        
        try:
            # Prepare features
            features = [normalize_arabic_text(text)]
            
            if merchant:
                features.append(f"merchant_{merchant.lower()}")
            if item:
                features.append(f"item_{item.lower()}")
            
            # Amount features
            if amount:
                if amount < 50:
                    features.append("amount_small")
                elif amount < 200:
                    features.append("amount_medium")
                elif amount < 500:
                    features.append("amount_large")
                else:
                    features.append("amount_very_large")
            
            feature_text = " ".join(features)
            
            # Predict
            prediction = self.pipeline.predict([feature_text])[0]
            probabilities = self.pipeline.predict_proba([feature_text])[0]
            
            # Get confidence (max probability)
            max_prob_idx = np.argmax(probabilities)
            confidence = probabilities[max_prob_idx]
            
            logger.debug(f"ML prediction: {prediction} (confidence: {confidence:.3f})")
            return prediction, confidence
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return None, 0.0
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the trained model"""
        if not self.is_trained:
            return {}
        
        try:
            # Get feature names and importance
            feature_names = self.vectorizer.get_feature_names_out()
            
            # For Naive Bayes, we can use feature log probabilities
            classifier = self.pipeline.named_steps['classifier']
            
            # Calculate average feature importance across all classes
            feature_importance = {}
            for i, feature in enumerate(feature_names):
                # Average log probability across classes
                avg_importance = np.mean(classifier.feature_log_prob_[:, i])
                feature_importance[feature] = float(avg_importance)
            
            # Sort by importance
            sorted_features = sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return dict(sorted_features[:50])  # Top 50 features
            
        except Exception as e:
            logger.error(f"Failed to get feature importance: {e}")
            return {}
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            import os
            os.makedirs("models", exist_ok=True)
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.pipeline, f)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _load_model(self):
        """Load trained model from disk"""
        try:
            import os
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.pipeline = pickle.load(f)
                self.is_trained = True
                logger.info(f"Model loaded from {self.model_path}")
            else:
                logger.info("No existing model found")
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.is_trained = False
    
    async def get_model_stats(self) -> Dict[str, Any]:
        """Get model statistics and performance metrics"""
        try:
            with get_db_session() as db:
                total_transactions = db.query(TransactionDB).count()
                total_feedback = db.query(UserFeedbackDB).count()
                
                # Category distribution
                category_dist = db.query(
                    TransactionDB.category,
                    db.func.count(TransactionDB.id).label('count')
                ).group_by(TransactionDB.category).all()
                
                return {
                    "is_trained": self.is_trained,
                    "model_path": self.model_path,
                    "total_transactions": total_transactions,
                    "total_feedback": total_feedback,
                    "category_distribution": [
                        {"category": cat, "count": count}
                        for cat, count in category_dist
                    ],
                    "supported_categories": self.categories
                }
                
        except Exception as e:
            logger.error(f"Failed to get model stats: {e}")
            return {"is_trained": self.is_trained, "error": str(e)}


class SmartCategoryPredictor:
    """Enhanced category prediction combining rule-based and ML approaches"""
    
    def __init__(self):
        self.ml_classifier = MLTransactionClassifier()
        self.rule_weights = {
            'keyword_match': 0.4,
            'merchant_match': 0.3,
            'amount_pattern': 0.1,
            'context_analysis': 0.2
        }
        self.ml_weight = 0.6  # Weight for ML prediction
        self.rule_weight = 0.4  # Weight for rule-based prediction
    
    async def predict_category(self, text: str, merchant: str = None, 
                             item: str = None, amount: float = None,
                             rule_based_category: str = None) -> Tuple[str, float]:
        """Predict category using hybrid approach"""
        
        # Get ML prediction
        ml_category, ml_confidence = self.ml_classifier.predict_category(
            text, merchant, item, amount
        )
        
        # If ML model is not available or low confidence, use rule-based
        if not ml_category or ml_confidence < 0.3:
            logger.debug("Using rule-based classification (ML unavailable or low confidence)")
            return rule_based_category or "Shopping", 0.7
        
        # If rule-based and ML agree, high confidence
        if ml_category == rule_based_category:
            combined_confidence = min(0.95, ml_confidence + 0.2)
            logger.debug(f"ML and rules agree: {ml_category} (confidence: {combined_confidence:.3f})")
            return ml_category, combined_confidence
        
        # If they disagree, use weighted combination
        if ml_confidence > 0.7:
            logger.debug(f"High ML confidence: {ml_category} (confidence: {ml_confidence:.3f})")
            return ml_category, ml_confidence
        else:
            # Use rule-based with moderate confidence
            logger.debug(f"Using rule-based due to ML uncertainty: {rule_based_category}")
            return rule_based_category or "Shopping", 0.6


# Global ML service instances
ml_classifier = MLTransactionClassifier()
smart_predictor = SmartCategoryPredictor()