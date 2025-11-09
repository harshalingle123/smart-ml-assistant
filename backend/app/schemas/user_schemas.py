from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from app.models.mongodb_models import PyObjectId


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., min_length=6)
    name: str = Field(..., description="Full name of the user")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: EmailStr
    name: str
    current_plan: str
    queries_used: int
    fine_tune_jobs: int
    datasets_count: int
    billing_cycle: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[PyObjectId] = None
