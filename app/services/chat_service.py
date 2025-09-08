from app.qaGptOss import process_query
from pydantic import BaseModel
from fastapi import Request, Response
import uuid
from sqlalchemy.orm import Session
import app.models as models
from datetime import datetime, timezone

# Định nghĩa schema cho request body
class UserQuery(BaseModel):
    id: str
    query: str

def chat(user_query: UserQuery):
    try:
        result = process_query(user_query.query)
        return {
            "EM": "Success",
            "EC": 0,
            "DT": result
        }
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        return  {
            "EC": 1,
            "EM": "Something wrong in chat service...",
            "DT": ""
        }
    
# assign cookie to user
def assign_cookie(response: Response, request: Request, db: Session):
    try:
        #gán cookie user_id nếu chưa có
        user_id = request.cookies.get("user_id")
        #print(">> check user cookies", user_id)
        if not user_id:
            user_id = str(uuid.uuid4()) #init user id
            response.set_cookie(key="user_id", value=user_id, max_age=60*60*24, httponly=True)
        
        # Save/update user in DB
        user = db.query(models.User).filter_by(id=user_id).first()
        if not user:
            user = models.User(id=user_id, first_seen=datetime.now(timezone.utc), last_seen=datetime.now(timezone.utc))
            db.add(user)
        else:
            user.last_seen = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "EM": "Success assign cookie!",
            "EC": 0,
            "DT": ""
        }
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        return  {
            "EC": 1,
            "EM": "Something wrong in chat service...",
            "DT": ""
        }