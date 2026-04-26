"""
Test MySQL Connection
Run this BEFORE starting the Streamlit app to verify your database setup.

Usage:
    python test_connection.py

Required Environment Variables:
    DB_USER         - Database username (e.g., avnadmin)
    DB_PASSWORD     - Database password
    DB_HOST         - Database host (e.g., mysql-yourproject.aivencloud.com)
    DB_PORT         - Database port (default: 24963 for Aiven)
    DB_NAME         - Database name (e.g., defaultdb)
    DB_SSL_CA       - Path to CA certificate file (default: ca.pem)

Windows CMD:
    set DB_USER=avnadmin
    set DB_PASSWORD=your_password
    set DB_HOST=mysql-yourproject.aivencloud.com
    set DB_PORT=24963
    set DB_NAME=defaultdb
    set DB_SSL_CA=ca.pem
    python test_connection.py

Windows PowerShell:
    $env:DB_USER="avnadmin"
    $env:DB_PASSWORD="your_password"
    $env:DB_HOST="mysql-yourproject.aivencloud.com"
    $env:DB_PORT="24963"
    $env:DB_NAME="defaultdb"
    $env:DB_SSL_CA="ca.pem"
    python test_connection.py
"""

import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Test 1: Check configuration values."""
    print("=" * 60)
    print("TEST 1: Configuration Check")
    print("=" * 60)

    from database import get_config_summary, DB_CONFIG

    config = get_config_summary()
    issues = []

    print(f"Host:     {config['host']}")
    if config['host'] in ['localhost', '']:
        issues.append("❌ Host is localhost. For Aiven, set DB_HOST environment variable.")
    else:
        print("✅ Host is set")

    print(f"Port:     {config['port']}")

    print(f"Database: {config['database']}")
    if config['database'] in ['your_database_name', '']:
        issues.append("❌ Database name not set. Set DB_NAME environment variable.")
    else:
        print("✅ Database name is set")

    print(f"Username: {config['username']}")
    if config['username'] in ['avnadmin'] and config['host'] not in ['localhost', '']:
        print("ℹ️  Using default username 'avnadmin'")

    print(f"SSL CA:   {config['ssl_ca']}")
    if config['ssl_ca_exists']:
        print("✅ SSL certificate file found")
    elif config['ssl_ca'] and config['ssl_ca'] != 'None':
        issues.append(f"❌ SSL certificate not found at: {config['ssl_ca']}")
        print("   💡 Download from Aiven console → Overview → CA Certificate")

    password = DB_CONFIG.get('password', '')
    if not password or password == 'your_database_password':
        issues.append("❌ Password not set. Set DB_PASSWORD environment variable.")
    else:
        print("✅ Password is set")

    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("\n✅ Configuration looks good!")
        return True

def test_connection():
    """Test 2: Try connecting to MySQL."""
    print("\n" + "=" * 60)
    print("TEST 2: Database Connection")
    print("=" * 60)

    from database import check_connection

    success, message = check_connection()
    print(message)
    return success

def test_tables():
    """Test 3: Check if tables can be created."""
    print("\n" + "=" * 60)
    print("TEST 3: Table Creation")
    print("=" * 60)

    try:
        from database import init_db, check_connection
        from models import Record

        success, msg = check_connection()
        if not success:
            print("❌ Cannot test tables - connection failed")
            return False

        init_db()
        print("✅ Tables created/verified successfully")
        print(f"   Table: {Record.__tablename__}")
        return True

    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

def test_crud():
    """Test 4: Basic CRUD operations."""
    print("\n" + "=" * 60)
    print("TEST 4: CRUD Operations")
    print("=" * 60)

    try:
        from database import SessionLocal
        from models import Record
        from schemas import RecordCreate
        from crud import create_record, get_record, delete_record

        db = SessionLocal()

        # Count before
        count_before = db.query(Record).count()
        print(f"Records before test: {count_before}")

        # Create test record
        test_data = RecordCreate(
            name="TEST_USER_DELETE_ME",
            email="test@example.com",
            category="Test",
            status="active"
        )
        record = create_record(db, test_data)
        print(f"✅ Created test record ID: {record.id}")

        # Read it back
        found = get_record(db, record.id)
        print(f"✅ Read record back: {found.name}")

        # Delete it
        deleted = delete_record(db, record.id)
        if deleted:
            print(f"✅ Deleted test record")

        # Verify deletion
        count_after = db.query(Record).count()
        print(f"Records after test: {count_after}")

        if count_before == count_after:
            print("✅ CRUD test passed - database is working!")
            return True
        else:
            print("⚠️  Record count mismatch - check manually")
            return False

    except Exception as e:
        print(f"❌ CRUD test failed: {e}")
        return False
    finally:
        db.close()

def main():
    """Run all tests."""
    print("\n" + "🧪 MySQL Connection Test Suite".center(60))
    print("Make sure environment variables are set first!\n")

    results = []

    # Run tests
    results.append(("Config", test_config()))
    results.append(("Connection", test_connection()))
    results.append(("Tables", test_tables()))
    results.append(("CRUD", test_crud()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<15} {status}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - You can now run: streamlit run app.py")
    else:
        print("⚠️  SOME TESTS FAILED - Fix issues above before running the app")
        print("\nQuick fixes:")
        print("  1. Set environment variables: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME")
        print("  2. Download ca.pem from Aiven console if using SSL")
        print("  3. Whitelist your IP in Aiven console → Allowed IP Addresses")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())