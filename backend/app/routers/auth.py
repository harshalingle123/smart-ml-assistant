from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.mongodb import mongodb
from app.models.mongodb_models import User
from app.schemas.user_schemas import UserCreate, UserLogin, UserResponse, Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.dependencies import get_current_user
from app.core.google_oauth import google_oauth
from bson import ObjectId
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    existing_user = await mongodb.database["users"].find_one({"email": user_data.email})

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        password=hashed_password,
    )

    result = await mongodb.database["users"].insert_one(new_user.dict(by_alias=True))
    new_user.id = result.inserted_id

    return UserResponse(**new_user.dict(by_alias=True))


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await mongodb.database["users"].find_one({"email": user_data.email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"Plain password from request: {user_data.password}")
    print(f"Hashed password from database: {user['password']}")

    if not verify_password(user_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict(by_alias=True))


@router.post("/google", response_model=Token)
async def google_login(token_request: GoogleTokenRequest):
    """
    Authenticate user with Google ID token

    This endpoint receives a Google ID token from the frontend,
    verifies it, and either creates a new user or logs in existing user.
    """
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

    # Check if user exists
    user = await mongodb.database["users"].find_one({"email": google_user["email"]})

    if user:
        # User exists, log them in
        access_token = create_access_token(data={"sub": str(user["_id"])})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        # New user, create account
        # Generate a random password (won't be used for Google OAuth users)
        import secrets
        random_password = secrets.token_urlsafe(32)

        new_user = User(
            email=google_user["email"],
            name=google_user["name"],
            password=get_password_hash(random_password),  # Store hashed random password
        )

        result = await mongodb.database["users"].insert_one(new_user.dict(by_alias=True))
        new_user.id = result.inserted_id

        # Create and return access token
        access_token = create_access_token(data={"sub": str(new_user.id)})
        return {"access_token": access_token, "token_type": "bearer"}
