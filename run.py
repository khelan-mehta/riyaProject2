#!/usr/bin/env python3
"""
Vehicle Parking App - Application Launcher
Run this file to start the Flask application
"""

import os
import sys
from app import app, init_db

def main():
    """Main function to run the application"""
    
    print("=" * 50)
    print("🚗 Vehicle Parking App - V1")
    print("=" * 50)
    
    # Initialize database
    print("📊 Initializing database...")
    try:
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    # Print application info
    print("\n📋 Application Information:")
    print(f"   • Framework: Flask")
    print(f"   • Database: SQLite")
    print(f"   • Frontend: HTML, CSS, Bootstrap")
    
    print("\n👤 Default Admin Credentials:")
    print(f"   • Username: admin")
    print(f"   • Password: admin123")
    
    print("\n🌐 Starting Flask application...")
    print(f"   • URL: http://localhost:5000")
    print(f"   • Environment: Development")
    print(f"   • Debug Mode: Enabled")
    
    print("\n💡 Tips:")
    print(f"   • Press Ctrl+C to stop the server")
    print(f"   • Database file: parking_app.db")
    print(f"   • Templates folder: templates/")
    
    print("\n" + "=" * 50)
    
    # Start the Flask application
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n\n❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()