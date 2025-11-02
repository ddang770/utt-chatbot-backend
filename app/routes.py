from fastapi import APIRouter, Depends, HTTPException, Security, Request, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.auth.util import get_current_admin
import app.services.admin_service as admin_service
from app.config.database import get_db
from typing import List, Optional
from app.schemas.admin import ChangePasswordSchema, AdminCreate
import app.auth.util as auth_util
from app.auth.admin_service import create_admin
from app.config_manager import load_config, save_config

# Create admin dependency
async def verify_admin(current_admin = Security(get_current_admin)):
    return current_admin

# Create an admin router with the security dependency
admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin)]
)

# get all file's name in data folder
@admin_router.get("/document/read")
def get_document_file(db: Session = Depends(get_db)):
    try:
        return admin_service.get_all_documents(db)
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))
    
@admin_router.get("/stats")
def get_stats(
    startDate: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    endDate: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    try:
        return admin_service.stats_service(startDate, endDate)
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))
    

@admin_router.post("/document/add")
async def add_documents(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    try:
        return await admin_service.add_documents(files, db)
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))
    
@admin_router.post("/document/delete")
async def delete_document(request: Request, db: Session = Depends(get_db)):
    try:
        return await admin_service.delete_document(request, db)
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        raise HTTPException(status_code=500, detail=str(e))
    
@admin_router.post("/change-password")
async def change_password(
    password_data: ChangePasswordSchema,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return await auth_util.change_admin_password(
        current_admin,
        password_data.current_password,
        password_data.new_password,
        db
    )

@admin_router.post("/register")
def register(admin: AdminCreate, db: Session = Depends(get_db)):
    created_admin = create_admin(
        db=db,
        username=admin.username,
        email=admin.email,
        password=admin.password
    )
    return {
        "EC": 0,
        "EM": "Create new user success!",
        "DT": {
            "username": created_admin.username,
            "email": created_admin.email,
            "last_login": created_admin.last_login,
            "formatted_last_login": created_admin.formatted_last_login
        }
    }


@admin_router.get("/documents/{doc_id}/generate_link")
def generate_doc_link(doc_id: int, current_admin = Depends(get_current_admin)):
    signed_url = admin_service.create_signed_url(doc_id, expires_in=180)
    return {
        "EC": 0,
        "EM": "Create signed url success!",
        "DT": {"url": signed_url}
    }

@admin_router.get("/chatbotcfg/get")
def chatbotcfg_get():
    cfg = load_config()
    return {
        "EC": 0,
        "EM": "Get chatbot cfg success!",
        "DT": cfg
    }

@admin_router.post("/chatbotcfg/post")
async def chatbotcfg_get(request: Request):
    data = await request.json()
    config = data.get("config", {})
    new_data = save_config(config)
    return {
        "EC": 0,
        "EM": "Update chatbot cfg success!",
        "DT": new_data
    }