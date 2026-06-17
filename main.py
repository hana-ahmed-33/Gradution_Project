"""
Main entry point for the Finance Analyzer application
"""
from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    from app.core.logging import get_logger
    
    logger = get_logger("main")
    logger.info(f"Starting Finance Analyzer on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True,
        reload=settings.debug
    )
