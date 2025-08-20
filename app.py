from config.cors import app
from pydantic import BaseModel
from services.chat_service import test_api
#from src.qaGptOss import process_query
from src.simpleChainGptOss import process_query
from fastapi import HTTPException

# Định nghĩa schema cho request body
class UserQuery(BaseModel):
    id: str
    query: str

# Route test
@app.get("/test_api")
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