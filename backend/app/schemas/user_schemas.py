from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.models.mongodb_models import PyObjectId
from app.core.validators import PasswordValidator, InputSanitizer


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., min_length=6, max_length=128, description="Password (minimum 6 characters)")
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Sanitize and validate name"""
        sanitized = InputSanitizer.sanitize_name(v)
        if len(sanitized) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return sanitized


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class SendOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email to send OTP to")
    purpose: str = Field(default="signup", description="Purpose: signup, password_reset, email_change")

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """Validate OTP purpose"""
        allowed_purposes = ['signup', 'password_reset', 'email_change', 'login']
        if v not in allowed_purposes:
            raise ValueError(f"Purpose must be one of: {', '.join(allowed_purposes)}")
        return v


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    purpose: str = Field(default="signup")


class CompleteRegistrationRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=2, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum requirements"""
        validation_result = PasswordValidator.validate_password(v)
        if not validation_result['valid']:
            raise ValueError('; '.join(validation_result['errors']))
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Sanitize and validate name"""
        sanitized = InputSanitizer.sanitize_name(v)
        if len(sanitized) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return sanitized


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetComplete(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum requirements"""
        validation_result = PasswordValidator.validate_password(v)
        if not validation_result['valid']:
            raise ValueError('; '.join(validation_result['errors']))
        return v


class UserResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: EmailStr
    name: str
    current_plan: str
    queries_used: int
    fine_tune_jobs: int
    datasets_count: int
    billing_cycle: Optional[str] = None
    email_verified: bool
    auth_provider: str
    account_status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {PyObjectId: str}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[PyObjectId] = None
