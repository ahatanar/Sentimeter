#!/usr/bin/env python3
"""
Script to retry failed journal entry enrichment jobs
"""

from src.app import create_app
from src.database import db
from src.models.journal_model import JournalEntryModel
from src.tasks.enrich import enrich_journal_entry

def retry_failed_entries():
    app = create_app()
    with app.app_context():
        failed_entries = db.session.query(JournalEntryModel).filter(
            JournalEntryModel.processing == True
        ).all()
        
        print(f"Found {len(failed_entries)} entries stuck in processing state")
        
        for entry in failed_entries:
            print(f"Retrying entry {entry.entry_id}: {entry.entry[:50]}...")
            
            entry.processing = True
            db.session.commit()
            
            enrich_journal_entry.delay(str(entry.entry_id))
            print(f"  → Queued for retry")
        
        print(f"\nSuccessfully queued {len(failed_entries)} entries for retry!")

if __name__ == "__main__":
    retry_failed_entries()