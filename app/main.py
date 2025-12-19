from app.config.cors import app
from pydantic import BaseModel
import app.services.admin_service as admin_service
import app.services.chat_service as chat_service
#from app.simpleChainGptOss import process_query
from fastapi import HTTPException, Request, Response, Depends, Query
from sqlalchemy.orm import Session
# from app.models import Message
from app.config.database import get_db
from app.vectorstore import VectorStore
from app.auth import routers
import app.routes as admin_router

# Load FAISS 1 lần khi app start
#@app.on_event("startup")
def load_faiss_index():
    VectorStore.get_instance()
    print("✅ FAISS index loaded and ready")

# Route test
@app.get("/")
def root():
    return {"Hello": "World"}

#import auth_router
app.include_router(routers.router)
#import /admin router
app.include_router(admin_router.admin_router)

# Định nghĩa schema cho request body
class UserQuery(BaseModel):
    id: str
    query: str

@app.post("/chat")
async def chat(request: Request):
    try:
        return await chat_service.chat(request)
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))
    
    
# Assign cookies to user
@app.get("/ck")
def assign_cookie(response: Response, request: Request, db: Session = Depends(get_db)):
    try:
        return chat_service.assign_cookie(response, request, db)

    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}/signed")
def view_doc_signed(doc_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    return admin_service.serve_signed_document(doc_id, token, db)