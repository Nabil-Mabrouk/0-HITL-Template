from pydantic import BaseModel, EmailStr, field_validator

class WaitlistCreate(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_not_disposable(cls, v: str) -> str:
        disposable = ["mailinator.com", "guerrillamail.com", "tempmail.com"]
        domain = v.split("@")[1].lower()
        if domain in disposable:
            raise ValueError("Les adresses email temporaires ne sont pas acceptées")
        return v.lower()

class WaitlistResponse(BaseModel):
    message: str