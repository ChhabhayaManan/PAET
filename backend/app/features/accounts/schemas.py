from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, validator
from typing import Optional, List, Dict, Literal
from datetime import datetime
from app.features.accounts.models import UserRole, SkillLevel


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)
    skill_level: Optional[str] = "beginner"  # beginner / intermediate / advanced
    preferred_languages: Optional[List[str]] = ["python"]
    interested_topics: Optional[List[str]] = []
    role: UserRole = UserRole.STUDENT

    @validator("password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─── User Profile Schemas ─────────────────────────────────────────────────────

class LearningProfileSchema(BaseModel):
    topic_scores: Dict[str, float] = {}
    error_patterns: List[str] = []
    strong_areas: List[str] = []
    weak_areas: List[str] = []
    recommended_next: List[str] = []
    preferred_content_types: List[str] = []
    study_time_preference: Optional[str] = None
    avg_problems_per_session: float = 0.0
    accuracy_rate: float = 0.0
    improvement_rate: float = 0.0
    profile_completeness: float = 0.0
    last_updated_by_agent: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    bio: Optional[str]
    avatar_url: Optional[str]
    institution: Optional[str]
    year_of_study: Optional[int]
    city: Optional[str]
    state: Optional[str]
    skill_level: SkillLevel
    years_of_experience: float
    preferred_languages: List[str]
    preferred_language: Literal["c", "cpp", "python"] = "c"
    interested_topics: Optional[List[str]] = []
    learning_goals: List[str]
    interests: List[str]
    total_sessions: int
    total_time_spent_mins: float
    points: int
    level: int
    badges: List[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    learning_profile: Optional[LearningProfileSchema]
    onboarding_done: bool = False

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    institution: Optional[str] = Field(None, max_length=255)
    year_of_study: Optional[int] = Field(None, ge=1, le=10)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    skill_level: Optional[SkillLevel] = None
    years_of_experience: Optional[float] = Field(None, ge=0.0, le=50.0)
    preferred_languages: Optional[List[str]] = None
    preferred_language: Optional[Literal["c", "cpp", "python"]] = None
    interested_topics: Optional[List[str]] = None
    learning_goals: Optional[List[str]] = None
    interests: Optional[List[str]] = None

    @field_validator("preferred_language")
    @classmethod
    def preferred_language_not_null(cls, v):
        if v is None:
            raise ValueError("preferred_language cannot be null")
        return v

    @validator("year_of_study", pre=True)
    def coerce_year_of_study(cls, v):
        if v == "" or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @validator("years_of_experience", pre=True)
    def coerce_years_of_experience(cls, v):
        if v == "" or v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator("new_password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ─── General Response Schemas ─────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ─── 2FA / OTP Schemas ────────────────────────────────────────────────────────

class OTPChallengeResponse(BaseModel):
    """Returned after successful password check — frontend must now submit OTP."""
    otp_token: str          # short-lived JWT (10 min), NOT an access token
    message: str = "OTP sent to your registered email address."
    email_hint: str         # e.g. "s***@gmail.com" — shows where OTP was sent


class VerifyOTPRequest(BaseModel):
    otp_token: str          # the otp_pending JWT from step 1
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


# ─── Forgot Password Schemas ──────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    otp_token: str
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator("new_password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ─── Profile / Mastery Schemas ────────────────────────────────────────────────

class TopicMasteryOut(BaseModel):
    topic: str
    label: str
    mastery: float
    evidence_count: int
    confidence: float
    band: str
    last_event_at: Optional[datetime] = None
    prerequisites: List[str]
    unlocked: bool


class MisconceptionCount(BaseModel):
    tag: str
    count: int


class LearningEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    item_id: Optional[int] = None
    topic: Optional[str] = None
    raw_topic: Optional[str] = None
    score: float
    weight: float
    hint_level_used: int
    misconceptions: List[str] = []
    mastery_before: Optional[float] = None
    mastery_after: Optional[float] = None
    source_ref: Optional[str] = None
    created_at: Optional[datetime] = None


class MasteryResponse(BaseModel):
    topics: List[TopicMasteryOut]
    top_misconceptions: List[MisconceptionCount]
    hint_reliance: float
    recent_events: List[LearningEventOut]
