import os
import logging
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env.dev')

logger = logging.getLogger(__name__)

def get_connection_string(use_psycopg3=False):
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = quote_plus(os.getenv('DB_PASSWORD', ''))
    db_name = os.getenv('DB_NAME', 'sales_copilot')
    
    driver = "psycopg" if use_psycopg3 else "psycopg2"
    return f"postgresql+{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Shared engine with optimized pooling
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        conn_str = get_connection_string(use_psycopg3=False)
        _engine = create_engine(
            conn_str,
            pool_size=5,            # Reduce pool size since multiple workers/modules exist
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,      # Recycle connections every 30 mins
            pool_pre_ping=True      # Check if connection is alive before using
        )
        logger.info("Database engine initialized")
    return _engine

# For things that specifically need psycopg3 (like langchain-postgres might prefer it)
_engine_v3 = None
def get_engine_v3():
    global _engine_v3
    if _engine_v3 is None:
        conn_str = get_connection_string(use_psycopg3=True)
        try:
            _engine_v3 = create_engine(
                conn_str,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True
            )
        except Exception:
            # Fallback to v2 if v3 driver not available
            logger.warning("Psycopg v3 driver not found, using v2 for all connections")
            _engine_v3 = get_engine()
    return _engine_v3
