# Endpoints, under /api/v1/auth:
#   POST /register         create an account
#   POST /login            check email + password, then email a one-time code
#   POST /verify-otp       check the one-time code, return access + refresh tokens
#   POST /forgot-password  email a one-time code for a password reset
#   POST /reset-password   check that code and set the new password
#   POST /refresh          swap a refresh token for a new access token
#   POST /logout           end the current session
#   GET  /me               the signed-in user
#   GET  /dev-login        whether the one-click dev login is switched on
#   POST /dev-login        sign in as DEV_LOGIN_EMAIL with no password (DEBUG only)

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.llm_choice import clear_cookie
from app.core.dependencies import get_current_active_user
from app.features.accounts.schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshTokenRequest, MessageResponse, UserProfileResponse,
    OTPChallengeResponse, VerifyOTPRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.core.config import settings
from app.features.accounts.service import AuthService
from app.features.accounts.models import User

import logging

logger=logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return AuthService.register(db, data)
    except Exception as e:
        logger.error(f"Error in register: {str(e)}")
        raise


@router.post(
    "/login",
    response_model=OTPChallengeResponse,
    summary="Step 1 — verify password, receive OTP via email",
)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Verifies email + password.
    On success: generates a 6-digit OTP, bcrypt-hashes it, stores the hash,
    emails the raw OTP to the user, and returns an otp_token (10-min JWT).
    The client must call /auth/verify-otp with that token + the OTP to get
    real access tokens.
    """
    return AuthService.login_step1(db, data)


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    summary="Step 2 — submit OTP, receive access + refresh tokens",
)
def verify_otp(data: VerifyOTPRequest, request: Request, db: Session = Depends(get_db)):
    """
    Verifies the 6-digit OTP against its bcrypt hash.
    On success: marks OTP as used and returns real JWT access + refresh tokens.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return AuthService.login_step2(
        db,
        otp_token  = data.otp_token,
        otp        = data.otp,
        ip_address = ip_address,
        user_agent = user_agent,
    )


@router.post(
    "/forgot-password",
    response_model=OTPChallengeResponse,
    summary="Request a password reset OTP",
)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Sends a 6-digit OTP to the email if it exists.
    Always returns 200 — never reveals whether the email is registered.
    """
    return AuthService.forgot_password(db, data.email)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Verify OTP and set new password",
)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Verifies the reset OTP and updates the password."""
    AuthService.reset_password(db, data.otp_token, data.otp, data.new_password)
    return MessageResponse(message="Password reset successfully. You can now log in.")


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    return AuthService.refresh_tokens(db, data.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout current session",
)
def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    AuthService.logout(db, current_user.id, jti="")
    clear_cookie(response)
    return MessageResponse(message="Successfully logged out.")


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get(
    "/dev-login",
    response_model=MessageResponse,
    summary="Is the dev login available?",
)
def dev_login_available():
    """Lets the login page decide whether to offer the button. The frontend is served
    as a production build, so it cannot tell from its own build flags."""
    if not (settings.DEBUG and settings.DEV_LOGIN_EMAIL):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return MessageResponse(message=settings.DEV_LOGIN_EMAIL)


@router.post(
    "/dev-login",
    response_model=TokenResponse,
    summary="Log in without a password or OTP (dev only)",
)
def dev_login(request: Request, db: Session = Depends(get_db)):
    """Returns tokens for DEV_LOGIN_EMAIL. 404 unless DEBUG is on and that is set."""
    return AuthService.dev_login(
        db,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
