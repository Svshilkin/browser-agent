"""
Main entry point for AI Browser Agent application.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings
from src.utils.logger import setup_logger, logger


async def main():
    """
    Main application entry point.
    
    This is where the CLI loop and agent execution would happen.
    For now, it's a placeholder that tests the configuration.
    """
    try:
        # Get settings
        settings = get_settings()
        
        logger.info("=" * 60)
        logger.info("Browser Agent")
        logger.info("=" * 60)
        
        # Display configuration
        logger.info(f"Browser: {settings.browser_type}")
        logger.info(f"Headless: {settings.headless}")
        logger.info(f"Max iterations: {settings.max_iterations}")
        logger.info(f"Log level: {settings.log_level}")
        logger.info(f"Project root: {settings.project_root}")
        
        logger.info("=" * 60)
        logger.info("Configuration loaded successfully!")
        logger.info("=" * 60)
        
        # Test log levels
        logger.debug("This is a DEBUG message (you won't see this in INFO mode)")
        logger.info("This is an INFO message")
        logger.warning("This is a WARNING message")
        
        logger.info("=" * 60)
        logger.info("Сompleted!")
        logger.info("=" * 60)
        
    except ValueError as e:
        logger.error(f"Configuration Error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run async main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nApplication interrupted by user")
        sys.exit(0)
