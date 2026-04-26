"""
MySQL Database Configuration - Aiven Compatible
Handles engine creation, session management, and table initialization.
Supports both local MySQL and Aiven Cloud (SSL required).
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import streamlit as st
import os

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION - UPDATE THESE VALUES
# ═══════════════════════════════════════════════════════════════

# Option 1: Aiven Cloud (RECOMMENDED)
# Get these from your Aiven console: https://console.aiven.io
DB_CONFIG = {
    "username": os.getenv("DB_USER", "avnadmin"),      # e.g., avnadmin
    "password": os.getenv("DB_PASSWORD", "your_database_password"),      # from Aiven console
    "host": os.getenv("DB_HOST", "localhost"),              # e.g., mysql-myproject.aivencloud.com
    "port": int(os.getenv("DB_PORT", 24963)),                          # Aiven default port (not 3306)
    "database": os.getenv("DB_NAME", "your_database_name"),       # your database name
    "ssl_ca": os.getenv("DB_SSL_CA", "ca.pem")                      # Download from Aiven console → Overview → CA Certificate
}

# Option 2: Local MySQL (comment out Option 1 and uncomment this)
# DB_CONFIG = {
#     "username": "app_user",
#     "password": "your_password",
#     "host": "localhost",
#     "port": 3306,
#     "database": "freelance_db",
#     "ssl_ca": None
# }

# ═══════════════════════════════════════════════════════════════
# ENGINE & SESSION SETUP
# ═══════════════════════════════════════════════════════════════

def create_engine_with_ssl():
    """Create SQLAlchemy engine with optional SSL for Aiven."""
    
    base_url = (
        f"mysql+pymysql://{DB_CONFIG['username']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset=utf8mb4"
    )
    
    connect_args = {}
    
    # Aiven requires SSL - configure if CA cert is provided
    if DB_CONFIG.get("ssl_ca") and os.path.exists(DB_CONFIG["ssl_ca"]):
        connect_args["ssl"] = {
            "ca": DB_CONFIG["ssl_ca"]
        }
    elif DB_CONFIG.get("ssl_ca"):
        # SSL is required but cert file not found - warn but still try
        print(f"⚠️  SSL CA certificate not found: {DB_CONFIG['ssl_ca']}")
        print("   Download it from Aiven console → Overview → CA Certificate")
    
    return create_engine(
        base_url,
        pool_pre_ping=True,       # Verify connections before using
        pool_recycle=3600,        # Recycle connections after 1 hour
        pool_size=5,              # Connection pool size
        max_overflow=10,          # Extra connections under load
        echo=False,               # Set True to debug SQL queries
        connect_args=connect_args
    )

engine = create_engine_with_ssl()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ═══════════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════

def get_db():
    """Yield a database session. Use in context managers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def check_connection():
    """Test MySQL connection. Returns (success: bool, message: str)."""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return True, "✅ Connected to MySQL (Aiven) successfully"
    except Exception as e:
        error_msg = str(e)
        if "SSL" in error_msg or "ssl" in error_msg:
            return False, f"❌ SSL Error: {error_msg}\n💡 Make sure ca.pem is downloaded from Aiven console"
        elif "Access denied" in error_msg:
            return False, f"❌ Access Denied: Check username/password in database.py"
        elif "Can't connect" in error_msg:
            return False, f"❌ Connection Failed: Check host/port. Aiven uses port 28863, not 3306"
        else:
            return False, f"❌ MySQL Connection Failed: {error_msg}"
