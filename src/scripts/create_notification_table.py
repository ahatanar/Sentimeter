#!/usr/bin/env python3
"""
Script to create the notification_settings table in the database.
Run this script after adding the NotificationSettings model.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import db
from src.models.notification_model import NotificationSettings
from src.models.user_model import User
from src.models.journal_model import JournalEntryModel


def create_notification_table():
    """Create the notification_settings table and add missing columns"""
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        from src.app import create_app
        
        app = create_app()
        with app.app_context():
            # Create the table
            NotificationSettings.__table__.create(db.engine, checkfirst=True)
            print("✅ notification_settings table created successfully!")
            
            # Add journal_day column if it doesn't exist
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'notification_settings' 
                AND column_name = 'journal_day'
            """))
            
            if not result.fetchone():
                db.session.execute(text("""
                    ALTER TABLE notification_settings 
                    ADD COLUMN journal_day VARCHAR(20) DEFAULT 'monday' NOT NULL
                """))
                db.session.commit()
                print("✅ journal_day column added successfully!")
            else:
                print("✅ journal_day column already exists!")
            
            # Verify the table exists
            result = db.session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'notification_settings')"))
            if result.scalar():
                print("✅ Table verification successful!")
            else:
                print("❌ Table verification failed!")
                
    except Exception as e:
        print(f"❌ Error creating notification_settings table: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Creating notification_settings table...")
    success = create_notification_table()
    if success:
        print("🎉 Database migration completed successfully!")
    else:
        print("💥 Database migration failed!")
        sys.exit(1) 