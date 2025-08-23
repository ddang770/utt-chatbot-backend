from app.config.cors import app
from pydantic import BaseModel
from app.services.chat_service import get_document_file_metadata
from app.services.admin_service import stats_service, message_service
#from app.qaGptOss import process_query
from app.simpleChainGptOss import process_query
from fastapi import HTTPException, Request, Response, Depends
import uuid
from sqlalchemy.orm import Session
from app.models import Message
from app.config.database import get_db

# Định nghĩa schema cho request body
class UserQuery(BaseModel):
    id: str
    query: str

# Route test
@app.get("/")
def root():
    return {"Hello": "World"}

# Route POST nhận JSON
@app.post("/chat")
def chat(user_query: UserQuery):
    try:
        result = process_query(user_query.query)
        return result
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))
    
# get all file's name in data folder
@app.get("/document_file")
def get_document_file():
    try:
        return get_document_file_metadata()
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))
    
# Assign cookies to user
@app.get("/ck")
def home(response: Response, request: Request):
    #gán cookie user_id nếu chưa có
    user_id = request.cookies.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4()) #init user id
        response.set_cookie(key="user_id", value=user_id, max_age=60*60*24*30, HttpOnly=False)
    return {"msg": "Welcome to Chatbot!"}


@app.get("/admin/stats")
def get_stats():
    try:
        return stats_service()
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/admin/message")
async def save_message(request: Request, db: Session = Depends(get_db)):
    try:
        return await message_service(request, db)
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))