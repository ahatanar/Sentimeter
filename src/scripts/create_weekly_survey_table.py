"""
Database migration script for WeeklySurvey feature.
Run this script to create the weekly_surveys table and update notification_settings.
"""

import os
import sys
from datetime import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app import create_app
from src.database import db
from src.models.weekly_survey_model import WeeklySurvey
from src.models.notification_model import NotificationSettings


def create_weekly_survey_table():
    """Create the weekly_surveys table"""
    try:
        # Create the table
        WeeklySurvey.__table__.create(db.engine, checkfirst=True)
        print("✅ Created weekly_surveys table")
        
        # Create index for efficient queries
        with db.engine.connect() as conn:
            conn.execute(db.text("""
                CREATE INDEX IF NOT EXISTS ix_survey_user_week 
                ON weekly_surveys (user_id, week_start)
            """))
            conn.commit()
        print("✅ Created index on weekly_surveys (user_id, week_start)")
        
    except Exception as e:
        print(f"❌ Error creating weekly_surveys table: {e}")
        raise


def add_survey_fields_to_notification_settings():
    """Add survey fields to notification_settings table"""
    try:
        with db.engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'notification_settings' 
                AND column_name IN ('survey_enabled', 'survey_day', 'survey_time')
            """))
            existing_columns = [row[0] for row in result]
            
            if 'survey_enabled' not in existing_columns:
                conn.execute(db.text("""
                    ALTER TABLE notification_settings 
                    ADD COLUMN survey_enabled BOOLEAN DEFAULT TRUE NOT NULL
                """))
                print("✅ Added survey_enabled column")
            
            if 'survey_day' not in existing_columns:
                conn.execute(db.text("""
                    ALTER TABLE notification_settings 
                    ADD COLUMN survey_day VARCHAR DEFAULT 'sunday' NOT NULL
                """))
                print("✅ Added survey_day column")
            
            if 'survey_time' not in existing_columns:
                conn.execute(db.text("""
                    ALTER TABLE notification_settings 
                    ADD COLUMN survey_time TIME DEFAULT '18:00:00' NOT NULL
                """))
                print("✅ Added survey_time column")
            
            conn.commit()
            print("✅ Updated notification_settings table with survey fields")
            
    except Exception as e:
        print(f"❌ Error updating notification_settings: {e}")
        raise


def main():
    """Run the migration"""
    print("🚀 Starting WeeklySurvey database migration...")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Create weekly_surveys table
            create_weekly_survey_table()
            
            # Add survey fields to notification_settings
            add_survey_fields_to_notification_settings()
            
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"💥 Migration failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main() 