"""
Test DATABASE_URL Connection
Run this locally to verify your DATABASE_URL works before deploying to Render.

Usage:
    python test_database_url.py

The script will:
1. Check if DATABASE_URL is set
2. Parse and validate the format
3. Try to connect to the database
4. Run a simple test query
"""

import os
import sys
from urllib.parse import urlparse

def test_database_url():
    print("=" * 60)
    print("DATABASE_URL Connection Test")
    print("=" * 60)
    
    # Step 1: Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL", "").strip()
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set!")
        print("\nTo set it (PowerShell):")
        print('  $env:DATABASE_URL = "postgresql://user:pass@host:5432/dbname"')
        print("\nTo set it (Command Prompt):")
        print('  set DATABASE_URL=postgresql://user:pass@host:5432/dbname')
        return False
    
    print("✓ DATABASE_URL is set")
    
    # Step 2: Parse the URL
    try:
        parsed = urlparse(db_url)
        print("\n--- Parsed Connection Details ---")
        print(f"  Scheme: {parsed.scheme}")
        print(f"  Host: {parsed.hostname}")
        print(f"  Port: {parsed.port or 'default'}")
        print(f"  Username: {parsed.username}")
        print(f"  Database: {parsed.path.lstrip('/')}")
        print(f"  Password: {'*' * len(parsed.password) if parsed.password else 'MISSING'}")
        
        # Validate basic requirements
        if parsed.scheme not in ["postgres", "postgresql"]:
            print(f"\n❌ ERROR: Invalid scheme '{parsed.scheme}'. Expected 'postgresql' or 'postgres'.")
            return False
        
        if not parsed.hostname:
            print("\n❌ ERROR: Missing hostname in DATABASE_URL")
            return False
        
        if not parsed.username:
            print("\n❌ ERROR: Missing username in DATABASE_URL")
            return False
        
        if not parsed.password:
            print("\n❌ ERROR: Missing password in DATABASE_URL")
            return False
        
        # Supabase-specific validation
        if "supabase.com" in parsed.hostname:
            print("\n--- Supabase Connection Detected ---")
            if "pooler.supabase.com" in parsed.hostname:
                print("⚠️  WARNING: You're using Supabase Pooler connection.")
                print("   Django works better with Direct Connection.")
                print("\n   Recommended format:")
                print("   postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres")
                
                if not parsed.username.startswith("postgres."):
                    print("\n❌ ERROR: Pooler requires username format 'postgres.[PROJECT_REF]'")
                    print(f"   Your username: '{parsed.username}'")
                    return False
            else:
                print("✓ Using Supabase Direct Connection (recommended)")
        
        print("\n✓ DATABASE_URL format validation passed")
        
    except Exception as e:
        print(f"\n❌ ERROR parsing DATABASE_URL: {e}")
        return False
    
    # Step 3: Try to connect
    print("\n--- Testing Database Connection ---")
    try:
        import dj_database_url
        import psycopg
        
        db_config = dj_database_url.parse(db_url)
        
        # Build connection string for psycopg
        conn_str = (
            f"host={db_config['HOST']} "
            f"port={db_config.get('PORT', 5432)} "
            f"dbname={db_config['NAME']} "
            f"user={db_config['USER']} "
            f"password={db_config['PASSWORD']}"
        )
        
        if 'sslmode' in db_url or 'supabase.com' in db_url:
            conn_str += " sslmode=require"
        
        print("Attempting connection...")
        conn = psycopg.connect(conn_str, connect_timeout=10)
        
        print("✓ Connected successfully!")
        
        # Step 4: Run test query
        print("\n--- Running Test Query ---")
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ PostgreSQL version: {version[:50]}...")
        
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        print(f"✓ Connected to database: {db_name}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYour DATABASE_URL is working correctly.")
        print("You can safely use this in Render's environment variables.")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ ERROR: Missing required package.")
        print(f"   {e}")
        print("\nInstall required packages:")
        print("   pip install dj-database-url psycopg[binary]")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: Connection failed!")
        print(f"   {type(e).__name__}: {e}")
        
        # Helpful hints based on error
        error_str = str(e).lower()
        print("\n--- Troubleshooting Hints ---")
        
        if "timeout" in error_str:
            print("• Connection timeout - check network/firewall")
            print("• Verify host is reachable")
            
        elif "authentication" in error_str or "password" in error_str:
            print("• Wrong username or password")
            print("• Double-check credentials in Supabase/Render dashboard")
            print("• If password has special chars (@, :, /, etc.), URL-encode them")
            
        elif "not found" in error_str or "enotfound" in error_str:
            print("• Database/user not found")
            print("• Verify project reference in connection string")
            print("• For Supabase: use Direct Connection, not Pooler")
            
        elif "ssl" in error_str:
            print("• SSL connection issue")
            print("• Add '?sslmode=require' to end of DATABASE_URL if not present")
        
        else:
            print("• Check DATABASE_URL format")
            print("• Verify database exists and is accessible")
            print("• Check Supabase/Render dashboard for connection details")
        
        return False


if __name__ == "__main__":
    print("\n")
    success = test_database_url()
    print("\n")
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)
