from pydantic import BaseModel, EmailStr
from datetime import datetime

class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AdminResponse(BaseModel):
    username: str
    email: str
    last_login: datetime | None = None
    formatted_last_login: str | None = None

    class Config:
        from_attributes = True
        from_attributes_defaults = True

class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str