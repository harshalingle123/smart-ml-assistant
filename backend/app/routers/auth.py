from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from app.mongodb import mongodb
from app.models.mongodb_models import User
from app.schemas.user_schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    SendOTPRequest, VerifyOTPRequest, CompleteRegistrationRequest,
    PasswordResetRequest, PasswordResetComplete
)
from app.core.security import get_password_hash, verify_password, create_access_token
from app.dependencies import get_current_user
from app.core.google_oauth import google_oauth
from app.core.email_service import email_service
from app.middleware.auth_rate_limiter import (
    rate_limit_by_ip, rate_limit_by_email, RateLimitConfig, get_client_ip
)
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    token: str


@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(request: Request, otp_request: SendOTPRequest):
    """
    Send OTP to email for verification.
    Used for: signup, password reset, email change.
    """
    # Rate limit by IP
    await rate_limit_by_ip(request, RateLimitConfig.SEND_OTP)

    # Rate limit by email
    await rate_limit_by_email(request, otp_request.email, RateLimitConfig.SEND_OTP)

    # For signup, check if email already exists (case-insensitive)
    if otp_request.purpose == "signup":
        existing_user = await mongodb.database["users"].find_one({
            "email": {"$regex": f"^{otp_request.email}$", "$options": "i"}
        })
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {otp_request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # For password reset, check if email exists (case-insensitive)
    if otp_request.purpose == "password_reset":
        user = await mongodb.database["users"].find_one({
            "email": {"$regex": f"^{otp_request.email}$", "$options": "i"}
        })
        if not user:
            # Don't reveal if email exists or not (security)
            logger.info(f"Password reset requested for non-existent email: {otp_request.email}")

    # Generate and send OTP
    otp = email_service.generate_otp()
    logger.info(f"Generated OTP for {otp_request.email}: {otp}")

    # Store OTP in database
    stored = await email_service.store_otp(otp_request.email, otp, otp_request.purpose)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OTP. Please try again."
        )

    # Send OTP email
    sent = await email_service.send_otp_email(otp_request.email, otp, otp_request.purpose)
    if not sent:
        logger.error(f"Failed to send OTP email to {otp_request.email}")

    return {
        "message": "OTP sent successfully. Please check your email.",
        "email": otp_request.email,
        "expires_in": 600  # 10 minutes
    }


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(request: Request, verify_request: VerifyOTPRequest):
    """
    Verify OTP code without completing registration.
    Returns verification status.
    """
    # Rate limit by IP
    await rate_limit_by_ip(request, RateLimitConfig.VERIFY_OTP)

    # Verify OTP
    result = await email_service.verify_otp(
        verify_request.email,
        verify_request.otp,
        verify_request.purpose
    )

    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return {
        "message": "OTP verified successfully",
        "verified": True
    }


@router.post("/register-direct", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_direct(request: Request, user_data: UserCreate):
    """
    DEVELOPMENT ONLY: Direct registration without OTP verification.
    For production, use the OTP-based flow: send-otp -> register

    This endpoint is for backward compatibility and testing.
    In production, disable this and use only the OTP flow.
    """
    # Rate limit by IP
    await rate_limit_by_ip(request, RateLimitConfig.REGISTER)

    # Check if user already exists (case-insensitive)
    existing_user = await mongodb.database["users"].find_one({
        "email": {"$regex": f"^{user_data.email}$", "$options": "i"}
    })
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user (without email verification in dev mode)
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email.lower(),  # Normalize email to lowercase
        name=user_data.name,
        password=hashed_password,
        email_verified=False,  # Not verified in direct registration
        auth_provider="email",
        account_status="active"  # Still activate for testing
    )

    try:
        result = await mongodb.database["users"].insert_one(new_user.dict(by_alias=True))
        new_user.id = result.inserted_id

        logger.info(f"New user registered (direct): {new_user.email}")

        return UserResponse(**new_user.dict(by_alias=True))

    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again."
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def complete_registration(request: Request, registration_data: CompleteRegistrationRequest):
    """
    PRODUCTION: Complete registration after OTP verification.
    This is the secure way to register - requires email verification.

    Flow: 1) POST /send-otp  2) POST /register with OTP
    """
    try:
        # Rate limit by IP
        await rate_limit_by_ip(request, RateLimitConfig.REGISTER)

        # Log registration attempt
        logger.info(f"Registration attempt for email: {registration_data.email}")

        # Verify OTP first
        otp_result = await email_service.verify_otp(
            registration_data.email,
            registration_data.otp,
            "signup"
        )

        if not otp_result["valid"]:
            logger.warning(f"Invalid OTP for registration: {registration_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=otp_result["message"]
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {registration_data.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

    # Check if user already exists (double-check, case-insensitive)
    existing_user = await mongodb.database["users"].find_one({
        "email": {"$regex": f"^{registration_data.email}$", "$options": "i"}
    })
    if existing_user:
        logger.warning(f"Registration completion attempt with existing email: {registration_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    hashed_password = get_password_hash(registration_data.password)
    new_user = User(
        email=registration_data.email.lower(),  # Normalize email to lowercase
        name=registration_data.name,
        password=hashed_password,
        email_verified=True,  # Email is verified via OTP
        auth_provider="email",
        account_status="active"  # Activate immediately after verification
    )

    try:
        result = await mongodb.database["users"].insert_one(new_user.dict(by_alias=True))
        new_user.id = result.inserted_id

        # Send welcome email
        await email_service.send_welcome_email(new_user.email, new_user.name)

        logger.info(f"New user registered: {new_user.email}")

        return UserResponse(**new_user.dict(by_alias=True))

    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again."
        )


@router.post("/login", response_model=Token)
async def login(request: Request, user_data: UserLogin):
    """
    Login with email and password.
    Includes account lockout protection after failed attempts.
    """
    # Rate limit by IP
    await rate_limit_by_ip(request, RateLimitConfig.LOGIN)

    # Rate limit by email
    await rate_limit_by_email(request, user_data.email, RateLimitConfig.LOGIN)

    # Case-insensitive email lookup for login
    user = await mongodb.database["users"].find_one({
        "email": {"$regex": f"^{user_data.email}$", "$options": "i"}
    })

    if not user:
        # Generic error message to prevent email enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is locked
    if user.get("account_locked_until"):
        lock_until = user["account_locked_until"]
        if datetime.utcnow() < lock_until:
            remaining_minutes = int((lock_until - datetime.utcnow()).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account temporarily locked due to too many failed login attempts. Try again in {remaining_minutes} minutes."
            )
        else:
            # Lock period expired, reset failed attempts
            await mongodb.database["users"].update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "failed_login_attempts": 0,
                        "account_locked_until": None
                    }
                }
            )
            user["failed_login_attempts"] = 0

    # Check if account is suspended
    if user.get("account_status") == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended. Please contact support."
        )

    # Check if email is verified (skip in development mode for testing)
    from app.core.config import settings
    if not user.get("email_verified") and settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )

    # Verify password
    if not verify_password(user_data.password, user["password"]):
        # Increment failed login attempts
        failed_attempts = user.get("failed_login_attempts", 0) + 1
        update_data = {
            "failed_login_attempts": failed_attempts,
            "last_login_attempt": datetime.utcnow()
        }

        # Lock account after 5 failed attempts
        if failed_attempts >= 5:
            lock_duration = timedelta(minutes=30)
            update_data["account_locked_until"] = datetime.utcnow() + lock_duration
            update_data["account_status"] = "locked"

            await mongodb.database["users"].update_one(
                {"_id": user["_id"]},
                {"$set": update_data}
            )

            logger.warning(f"Account locked for {user_data.email} after {failed_attempts} failed attempts")

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed login attempts. Please try again in 30 minutes or reset your password."
            )

        await mongodb.database["users"].update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )

        remaining_attempts = 5 - failed_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password. {remaining_attempts} attempts remaining.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful login - reset failed attempts and update last login
    await mongodb.database["users"].update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "failed_login_attempts": 0,
                "last_login_at": datetime.utcnow(),
                "last_login_attempt": datetime.utcnow(),
                "account_locked_until": None
            }
        }
    )

    logger.info(f"Successful login for {user_data.email}")

    access_token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict(by_alias=True))


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(request: Request, reset_request: PasswordResetRequest):
    """
    Request password reset OTP.
    Sends OTP to email if account exists.
    """
    # Rate limit by IP
    await rate_limit_by_ip(request, RateLimitConfig.PASSWORD_RESET)

    # Rate limit by email
    await rate_limit_by_email(request, reset_request.email, RateLimitConfig.PASSWORD_RESET)

    # Check if user exists (but don't reveal in response for security, case-insensitive)
    user = await mongodb.database["users"].find_one({
        "email": {"$regex": f"^{reset_request.email}$", "$options": "i"}
    })

    if user:
        # Generate and send OTP
        otp = email_service.generate_otp()
        logger.info(f"Password reset OTP for {reset_request.email}: {otp}")

        # Store OTP
        await email_service.store_otp(reset_request.email, otp, "password_reset")

        # Send OTP email
        await email_service.send_otp_email(reset_request.email, otp, "password_reset")

    # Always return success to prevent email enumeration
    return {
        "message": "If an account exists with this email, a password reset code has been sent.",
        "email": reset_request.email
    }


@router.post("/password-reset/complete", status_code=status.HTTP_200_OK)
async def complete_password_reset(request: Request, reset_data: PasswordResetComplete):
    """
    Complete password reset with OTP and new password.
    """
    # Rate limit by IP
    await rate_limit_by_ip(request, RateLimitConfig.VERIFY_OTP)

    # Verify OTP
    otp_result = await email_service.verify_otp(
        reset_data.email,
        reset_data.otp,
        "password_reset"
    )

    if not otp_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=otp_result["message"]
        )

    # Find user (case-insensitive)
    user = await mongodb.database["users"].find_one({
        "email": {"$regex": f"^{reset_data.email}$", "$options": "i"}
    })
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password and unlock account if locked
    hashed_password = get_password_hash(reset_data.new_password)
    await mongodb.database["users"].update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password": hashed_password,
                "failed_login_attempts": 0,
                "account_locked_until": None,
                "account_status": "active" if user.get("account_status") == "locked" else user.get("account_status", "active"),
                "updated_at": datetime.utcnow()
            }
        }
    )

    logger.info(f"Password reset completed for {reset_data.email}")

    return {
        "message": "Password reset successfully. You can now login with your new password."
    }


@router.post("/google", response_model=Token)
async def google_login(request: Request, token_request: GoogleTokenRequest):
    """
    Authenticate user with Google ID token.
    Verifies token and either creates new user or logs in existing user.
    """
    # Rate limit by IP
    await rate_limit_by_ip(request, RateLimitConfig.GOOGLE_OAUTH)

    # Verify Google token
    google_user = await google_oauth.verify_google_token(token_request.token)

    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if email is verified
    if not google_user.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email not verified"
        )

    # Check if user exists (case-insensitive)
    user = await mongodb.database["users"].find_one({
        "email": {"$regex": f"^{google_user['email']}$", "$options": "i"}
    })

    if user:
        # User exists - update last login and Google ID if not set
        update_data = {
            "last_login_at": datetime.utcnow(),
            "last_login_attempt": datetime.utcnow()
        }

        # If user originally signed up with email but now using Google, update auth provider
        if user.get("auth_provider") == "email" and not user.get("oauth_id"):
            update_data["auth_provider"] = "google"
            update_data["oauth_id"] = google_user.get("google_id")

        await mongodb.database["users"].update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )

        logger.info(f"Google login successful for existing user: {user['email']}")

        access_token = create_access_token(data={"sub": str(user["_id"])})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        # New user - create account
        import secrets
        random_password = secrets.token_urlsafe(32)

        new_user = User(
            email=google_user["email"].lower(),  # Normalize email to lowercase
            name=google_user["name"],
            password=get_password_hash(random_password),  # Store hashed random password
            email_verified=True,  # Google emails are verified
            auth_provider="google",
            oauth_id=google_user.get("google_id"),
            account_status="active"  # Activate immediately for OAuth users
        )

        try:
            result = await mongodb.database["users"].insert_one(new_user.dict(by_alias=True))
            new_user.id = result.inserted_id

            # Send welcome email
            await email_service.send_welcome_email(new_user.email, new_user.name)

            logger.info(f"New user created via Google OAuth: {new_user.email}")

            # Create and return access token
            access_token = create_access_token(data={"sub": str(new_user.id)})
            return {"access_token": access_token, "token_type": "bearer"}

        except Exception as e:
            logger.error(f"Failed to create Google OAuth user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account. Please try again."
            )
