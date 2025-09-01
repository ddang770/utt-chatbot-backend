from app.qaGptOss import process_query
from pydantic import BaseModel
from fastapi import Request, Response
import uuid

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
def assign_cookie(response: Response, request: Request):
    try:
        #gán cookie user_id nếu chưa có
        user_id = request.cookies.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4()) #init user id
            response.set_cookie(key="user_id", value=user_id, max_age=60*60*24*30, HttpOnly=False)
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