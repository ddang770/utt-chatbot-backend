from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Admin
from app.auth.util import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

def create_admin(db: Session, username: str, password: str):
    hashed_password = get_password_hash(password)
    db_admin = Admin(username=username, password=hashed_password)
    db.add(db_admin)
    try:
        db.commit()
        db.refresh(db_admin)
        return db_admin
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

def authenticate_admin(db: Session, username: str, password: str):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}