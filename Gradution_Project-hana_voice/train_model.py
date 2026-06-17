#!/usr/bin/env python3
"""
ML Model training script for Finance Analyzer
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ml_service import ml_classifier
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("model_training")

async def main():
    """Train the ML model with available data"""
    try:
        logger.info("Starting ML model training...")
        
        # Get model stats before training
        stats_before = await ml_classifier.get_model_stats()
        logger.info(f"📊 Pre-training stats: {stats_before}")
        
        # Train model
        result = await ml_classifier.train_model(min_samples=10)  # Lower threshold for demo
        
        if result["success"]:
            logger.info("✅ Model training completed successfully!")
            logger.info(f"📈 Accuracy: {result['accuracy']:.3f}")
            logger.info(f"📊 Training samples: {result['train_samples']}")
            logger.info(f"🧪 Test samples: {result['test_samples']}")
            
            # Get feature importance
            importance = ml_classifier.get_feature_importance()
            if importance:
                logger.info("🔍 Top 10 important features:")
                for i, (feature, score) in enumerate(list(importance.items())[:10]):
                    logger.info(f"  {i+1}. {feature}: {score:.3f}")
            
            return True
        else:
            logger.warning(f"⚠️ Model training failed: {result.get('message', 'Unknown error')}")
            logger.info(f"📊 Available samples: {result.get('samples_count', 0)}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Model training failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)