import os
import logging
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env.dev')

logger = logging.getLogger(__name__)

from sqlalchemy.pool import NullPool

def get_connection_string(use_psycopg3=False):
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = quote_plus(os.getenv('DB_PASSWORD', ''))
    db_name = os.getenv('DB_NAME', 'sales_copilot')
    
    driver = "psycopg" if use_psycopg3 else "psycopg2"
    return f"postgresql+{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Shared engine with micro-pooling to balance efficiency and connection limits
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        conn_str = get_connection_string(use_psycopg3=False)
        # pool_size=2 per worker. With 10 workers, this uses 20 connections max.
        # max_overflow=0 ensures we never exceed the limit.
        _engine = create_engine(
            conn_str,
            pool_size=2,
            max_overflow=0,
            pool_timeout=20,
            pool_recycle=2000,
            pool_pre_ping=True
        )
        logger.info("Database engine initialized with micro-pool (size=2)")
    return _engine

# For things that specifically need psycopg3
_engine_v3 = None
def get_engine_v3():
    global _engine_v3
    if _engine_v3 is None:
        conn_str = get_connection_string(use_psycopg3=True)
        try:
            _engine_v3 = create_engine(
                conn_str,
                pool_size=2,
                max_overflow=0,
                pool_timeout=20,
                pool_recycle=2000,
                pool_pre_ping=True
            )
        except Exception:
            logger.warning("Psycopg v3 driver not found, using v2 for all connections")
            _engine_v3 = get_engine()
    return _engine_v3
