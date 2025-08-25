from sqlalchemy import Column, Integer, String, DateTime, func
from app.config.database import Base
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # metadata fields
    name = Column(String, nullable=False)         # "name_file.md"
    size = Column(String, unique=True, nullable=False)         # "166.0 KB"
    upload_date = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(String, default="pending")    # "processed" | "pending" | "failed"
    type = Column(String, nullable=False)         # "MD" | "PDF" | ...
    vector_ids = Column(JSONB, nullable=True) 
