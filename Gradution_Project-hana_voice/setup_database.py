#!/usr/bin/env python3
"""
Database setup script for Finance Analyzer
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import create_tables, db_manager
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("database_setup")

def main():
    """Setup database tables and initial data"""
    try:
        logger.info("Setting up Finance Analyzer database...")
        
        # Create tables
        create_tables()
        logger.info("✅ Database tables created successfully")
        
        # Test database connection
        if db_manager.health_check():
            logger.info("✅ Database connection test passed")
        else:
            logger.error("❌ Database connection test failed")
            return False
        
        # Get initial stats
        stats = db_manager.get_stats()
        logger.info(f"📊 Database stats: {stats}")
        
        logger.info("🎉 Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)