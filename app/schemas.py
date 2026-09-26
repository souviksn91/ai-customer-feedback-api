from pydantic import BaseModel, EmailStr, Field, model_validator


class UserRegister(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)

    # validates that two passwords match
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self

    

class UserLogin(BaseModel):
    email: EmailStr
    password: str