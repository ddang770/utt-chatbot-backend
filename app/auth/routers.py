from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.admin import AdminCreate, AdminLogin, Token, AdminResponse
from app.auth.admin_service import create_admin, authenticate_admin
from app.auth.util import get_current_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])

# @router.post("/register", response_model=AdminResponse)
# def register(admin: AdminCreate, db: Session = Depends(get_db)):
#     return create_admin(
#         db=db,
#         username=admin.username,
#         email=admin.email,
#         password=admin.password
#     )

@router.post("/login", response_model=Token)
def login(admin: AdminLogin, db: Session = Depends(get_db)):
    return authenticate_admin(db, admin.email, admin.password)

@router.get("/me", response_model=AdminResponse)
def read_users_me(current_admin = Depends(get_current_admin)):
    return current_admin