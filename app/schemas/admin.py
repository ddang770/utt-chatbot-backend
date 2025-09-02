from pydantic import BaseModel

class AdminCreate(BaseModel):
    username: str
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AdminResponse(BaseModel):
    username: str
    
    class Config:
        from_attributes = True