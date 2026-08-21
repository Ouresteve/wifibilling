from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.schemas import MpesaSettingsUpdate, MpesaSettingsOut
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, UserOut, Token
from app.core.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        phone=user_in.phone,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}



@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user







@router.get("/mpesa-settings", response_model=MpesaSettingsOut)
def get_mpesa_settings(current_user: User = Depends(get_current_user)):
    return MpesaSettingsOut(
        mpesa_shortcode=current_user.mpesa_shortcode,
        mpesa_consumer_key=current_user.mpesa_consumer_key,
        has_consumer_secret=bool(current_user.mpesa_consumer_secret),
        has_passkey=bool(current_user.mpesa_passkey),
        is_configured=bool(
            current_user.mpesa_shortcode
            and current_user.mpesa_consumer_key
            and current_user.mpesa_consumer_secret
            and current_user.mpesa_passkey
        ),
    )


@router.put("/mpesa-settings", response_model=MpesaSettingsOut)
def update_mpesa_settings(
    data: MpesaSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.mpesa_shortcode is not None:
        current_user.mpesa_shortcode = data.mpesa_shortcode.strip() or None
    if data.mpesa_consumer_key is not None:
        current_user.mpesa_consumer_key = data.mpesa_consumer_key.strip() or None
    if data.mpesa_consumer_secret is not None:
        current_user.mpesa_consumer_secret = data.mpesa_consumer_secret.strip() or None
    if data.mpesa_passkey is not None:
        current_user.mpesa_passkey = data.mpesa_passkey.strip() or None

    db.commit()
    db.refresh(current_user)

    return MpesaSettingsOut(
        mpesa_shortcode=current_user.mpesa_shortcode,
        mpesa_consumer_key=current_user.mpesa_consumer_key,
        has_consumer_secret=bool(current_user.mpesa_consumer_secret),
        has_passkey=bool(current_user.mpesa_passkey),
        is_configured=bool(
            current_user.mpesa_shortcode
            and current_user.mpesa_consumer_key
            and current_user.mpesa_consumer_secret
            and current_user.mpesa_passkey
        ),
    )