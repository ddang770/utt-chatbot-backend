from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models import Admin
from app.auth.util import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

def create_admin(db: Session, username: str, email: str, password: str):
    try:
        # Check if username or email already exists
        existing_admin = db.query(Admin).filter(
            (Admin.username == username) | (Admin.email == email)
        ).first()
        
        if existing_admin:
            if existing_admin.username == username:
                raise HTTPException(status_code=400, detail="Username already exists")
            raise HTTPException(status_code=400, detail="Email already exists")

        hashed_password = get_password_hash(password)
        db_admin = Admin(
            username=username,
            email=email,
            password=hashed_password,
            last_login=datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        )
        
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        return db_admin

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {str(e)}")  # For debugging
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def authenticate_admin(db: Session, email: str, password: str):
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin or not verify_password(password, admin.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Update last login time
    admin.last_login = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}