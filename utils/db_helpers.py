"""
Database helper utilities for connection management
"""
import time
import logging
from functools import wraps
from sqlalchemy.exc import OperationalError, DisconnectionError
from models.database import db

logger = logging.getLogger(__name__)

def db_retry(max_retries=3, delay=1.0):
    """
    Decorator to retry database operations on connection failures
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        try:
                            db.session.rollback()
                            db.session.remove()
                        except:
                            pass
                    else:
                        logger.error(f"Database connection failed after {max_retries} attempts: {str(e)}")
                except Exception as e:
                    # Non-connection errors should be raised immediately
                    raise e
            
            # If we get here, all retries failed
            raise last_exception
            
        return wrapper
    return decorator

def safe_db_operation(operation_func, fallback_value=None):
    """
    Execute database operation with fallback on connection failure
    """
    try:
        return operation_func()
    except (OperationalError, DisconnectionError) as e:
        logger.error(f"Database operation failed: {str(e)}")
        try:
            db.session.rollback()
            db.session.remove()
        except:
            pass
        return fallback_value
    except Exception as e:
        logger.error(f"Unexpected database error: {str(e)}")
        raise e