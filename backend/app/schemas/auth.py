from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email:            EmailStr
    password:         str
    full_name:        str | None = None
    invitation_token: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Minimum 8 caractères")
        if not any(c.isupper() for c in v):
            raise ValueError("Au moins une majuscule requise")
        if not any(c.isdigit() for c in v):
            raise ValueError("Au moins un chiffre requis")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str | None = None
    token_type:    str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class MessageResponse(BaseModel):
    message: str

class RegisterDirectRequest(BaseModel):
    email:     EmailStr
    password:  str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Minimum 8 caractères")
        if not any(c.isupper() for c in v):
            raise ValueError("Au moins une majuscule requise")
        if not any(c.isdigit() for c in v):
            raise ValueError("Au moins un chiffre requis")
        return v