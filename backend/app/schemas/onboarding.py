from pydantic import BaseModel, EmailStr, Field
from typing import Dict

class OnboardingRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    answers: Dict[str, str]

class OnboardingEvaluateRequest(BaseModel):
    answers: Dict[str, str]

class OnboardingUpdateProfileRequest(BaseModel):
    answers: Dict[str, str]
