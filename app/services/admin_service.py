from app.models import Message
from app.config.database import get_db
from fastapi import  Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from app.config.database import SessionLocal

# Get user message and save to database for admin monitor
async def message_service(request: Request, db: Session):
    #Nhận message từ user, lưu DB
    user_id = request.cookies.get("user_id") or str(uuid.uuid4())
    data = await request.json()
    msg = data.get("message", "")

    new_msg = Message(user_id=user_id, message=msg)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    return {"reply": f"Bot received: {msg}"}

# Thống kê cho admin
def stats_service():
    db = SessionLocal()
    try:
        total_users = db.query(Message.user_id).distinct().count()

        todays_users = (
            db.query(Message.user_id)
            .filter(func.date(Message.created_at) == func.current_date())
            .distinct()
            .count()
        )

        num_messages = db.query(Message).count()

        return {
            "EM": "Get stats data success!",
            "EC": 0,
            "DT": {
                "total_users": total_users,
                "todays_users": todays_users,
                "num_messages": num_messages
            }
            
        }
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        return  {
            "EC": 1,
            "EM": "Something wrong in admin service...",
            "DT": {}
        }
    finally:
        db.close()