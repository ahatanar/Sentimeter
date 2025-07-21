from src.models.journal_model import JournalEntryModel
from src.database import db
from sqlalchemy import or_, text
from src.app import create_app

def add_columns():
    with db.engine.connect() as conn:
        # Add 'processing' column (boolean, default True)
        conn.execute(text("""
            ALTER TABLE journals
            ADD COLUMN IF NOT EXISTS processing BOOLEAN DEFAULT TRUE
        """))
        # Add 'last_enriched_at' column (timestamp, nullable)
        conn.execute(text("""
            ALTER TABLE journals
            ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMPTZ NULL
        """))
        # Add 'ip_address' column (string, nullable)
        conn.execute(text("""
            ALTER TABLE journals
            ADD COLUMN IF NOT EXISTS ip_address VARCHAR NULL
        """))
        # Add index on processing
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_journals_processing ON journals(processing)
        """))
    print("Columns added (if they did not already exist).")

def backfill_processing_fields():
    entries = db.session.query(JournalEntryModel).filter(
        or_(JournalEntryModel.processing == None, JournalEntryModel.last_enriched_at == None)
    ).all()
    print(f"Found {len(entries)} entries to backfill.")
    for entry in entries:
        entry.processing = False
        if not entry.last_enriched_at:
            entry.last_enriched_at = entry.timestamp
    db.session.commit()
    print("Backfill complete.")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        add_columns()
        backfill_processing_fields() 