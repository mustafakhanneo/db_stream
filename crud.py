"""
CRUD Operations
All database interactions for the Record model.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models import Record
from schemas import RecordCreate, RecordUpdate
from typing import List, Optional

def create_record(db: Session, record: RecordCreate) -> Record:
    """Create a new record."""
    db_record = Record(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_record(db: Session, record_id: int) -> Optional[Record]:
    """Get a single record by ID."""
    return db.query(Record).filter(Record.id == record_id).first()

def get_records(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> tuple[List[Record], int]:
    """
    Get records with filtering and pagination.
    Returns: (records_list, total_count)
    """
    query = db.query(Record)

    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Record.name.like(search_filter)) |
            (Record.email.like(search_filter)) |
            (Record.notes.like(search_filter))
        )

    if category:
        query = query.filter(Record.category == category)

    if status:
        query = query.filter(Record.status == status)

    if date_from:
        query = query.filter(func.date(Record.date) >= date_from)

    if date_to:
        query = query.filter(func.date(Record.date) <= date_to)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    records = query.order_by(desc(Record.created_at)).offset(skip).limit(limit).all()

    return records, total

def update_record(db: Session, record_id: int, record_update: RecordUpdate) -> Optional[Record]:
    """Update an existing record."""
    db_record = get_record(db, record_id)
    if not db_record:
        return None

    update_data = record_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_record, field, value)

    db.commit()
    db.refresh(db_record)
    return db_record

def delete_record(db: Session, record_id: int) -> bool:
    """Delete a record. Returns True if deleted, False if not found."""
    db_record = get_record(db, record_id)
    if not db_record:
        return False

    db.delete(db_record)
    db.commit()
    return True

def get_categories(db: Session) -> List[str]:
    """Get all unique categories."""
    categories = db.query(Record.category).distinct().all()
    return [cat[0] for cat in categories if cat[0]]

def get_statuses(db: Session) -> List[str]:
    """Get all unique statuses."""
    statuses = db.query(Record.status).distinct().all()
    return [stat[0] for stat in statuses if stat[0]]

def bulk_create_records(db: Session, records_data: List[dict]) -> int:
    """Bulk insert records. Returns number of records inserted."""
    db_records = [Record(**data) for data in records_data]
    db.bulk_save_objects(db_records)
    db.commit()
    return len(db_records)
