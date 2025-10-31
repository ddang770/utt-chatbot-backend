from typing import List, Dict
from app.config.database import SessionLocal
from app.models import Message
from sqlalchemy import asc
import uuid

class PostgresChatMessageHistory:
    """
    Minimal ChatMessageHistory compatible with ConversationBufferMemory:
    required methods used below: add_user_message, add_ai_message, get_messages, clear
    """
    def __init__(self, user_id: str):
        # user_id expected as string UUID
        try:
            self.user_uuid = uuid.UUID(user_id)
        except Exception:
            self.user_uuid = user_id
        self.db = SessionLocal()

    def add_user_message(self, text: str):
        m = Message(user_id=self.user_uuid, message=text, role="user")
        self.db.add(m)
        self.db.commit()

    def add_ai_message(self, text: str):
        m = Message(user_id=self.user_uuid, message=text, role="assistant")
        self.db.add(m)
        self.db.commit()

    def get_messages(self, limit: int | None = None) -> List[Dict]:
        q = self.db.query(Message).filter(Message.user_id == self.user_uuid).order_by(asc(Message.created_at))
        if limit:
            q = q.limit(limit)
        rows = q.all()
        return [{"role": r.role, "content": r.message, "created_at": r.created_at} for r in rows]

    def clear(self):
        self.db.query(Message).filter(Message.user_id == self.user_uuid).delete()
        self.db.commit()

    def close(self):
        self.db.close()